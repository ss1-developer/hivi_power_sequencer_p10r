import asyncio
import logging
import time
from typing import Callable, Optional, Awaitable, Dict, TypedDict
import threading
from collections import defaultdict

_LOGGER = logging.getLogger(__name__)


class DebugStats(TypedDict):
    created_count: int
    destroyed_count: int
    send_count: int
    receive_count: int
    connect_attempts: int
    last_activity: Optional[float]


class TCPClient:
    _instances: Dict[str, "TCPClient"] = {}  # 使用defaultdict来存储每个IP地址对应的实例
    _lock = threading.Lock()  # 用于线程安全

    # 调试统计信息
    _debug_stats: Dict[str, DebugStats] = defaultdict(
        lambda: {
            "created_count": 0,
            "destroyed_count": 0,
            "send_count": 0,
            "receive_count": 0,
            "connect_attempts": 0,
            "last_activity": None,
        }
    )

    @staticmethod
    def get_instance(host, port) -> Optional["TCPClient"]:
        """
        根据IP地址获取TcpConnectionManager的实例。
        如果给定IP地址的实例不存在，则创建一个新的实例并返回。
        """
        _LOGGER.debug(
            f"{threading.current_thread().ident} TcpConnectionManager get_instance"
        )
        key = f"{host}_{port}"
        with TCPClient._lock:
            if key not in TCPClient._instances:
                _LOGGER.debug("No such client will create")
                TCPClient._instances[key] = TCPClient(host, port)
                TCPClient._debug_stats[key]["created_count"] += 1
                TCPClient._debug_stats[key]["last_activity"] = time.time()
            else:
                _LOGGER.debug("Already has such client")
            return TCPClient._instances[key]

    @staticmethod
    def get_debug_info():
        """获取所有实例的调试信息"""
        with TCPClient._lock:
            instances_info = {}
            for key, instance in TCPClient._instances.items():
                if instance is not None:
                    instances_info[key] = {
                        "is_connected": instance._is_connected,
                        "connect_attempts": instance._connect_attempts,
                        "queue_size": instance._queue.qsize(),
                        "is_running": instance._is_running,
                        "should_stop": instance._should_stop,
                    }

            return {
                "total_instances": len(
                    [v for v in TCPClient._instances.values() if v is not None]
                ),
                "instances_info": instances_info,
                "debug_stats": dict(TCPClient._debug_stats),
            }

    def __init__(
        self,
        host: str,
        port: int,
        *,
        max_retry_interval: float = 10.0,  # 最大重试间隔(秒)
        initial_retry_interval: float = 5.0,  # 初始重试间隔
        connection_timeout: float = 10.0,  # 连接超时
    ):
        self._host = host
        self._port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._callback: Optional[Callable[[bytes], None]] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._is_connected = False
        self._should_stop = False
        self._queue = asyncio.Queue()
        self._send_loop_task = None
        self._is_running = True

        # 重试配置
        self._max_retry_interval = max_retry_interval
        self._initial_retry_interval = initial_retry_interval
        self._current_retry_interval = initial_retry_interval
        self._connection_timeout = connection_timeout

        # 统计信息
        self._last_connect_time: Optional[float] = None
        self._connect_attempts = 0
        self._last_send_time: Optional[float] = None
        self._last_receive_time: Optional[float] = None

        # connect
        # 在后台启动连接任务
        self._reconnect_task = asyncio.create_task(self._auto_reconnect())
        # self._send_loop_task = asyncio.create_task(self._send_loop())

        _LOGGER.debug(f"TCPClient initialized for {host}:{port}")

    @property
    def is_connected(self) -> bool:
        """返回当前连接状态"""
        return self._is_connected

    @property
    def host(self) -> str:
        """返回IP地址"""
        return self._host

    @property
    def port(self) -> int:
        """返回端口号"""
        return self._port

    @property
    def queue_size(self) -> int:
        """返回队列大小"""
        return self._queue.qsize()

    async def connect(self) -> None:
        """启动连接（自动重连）"""
        _LOGGER.debug(f"connect called for {self._host}:{self._port}")
        if self._reconnect_task and not self._reconnect_task.done():
            _LOGGER.debug("Reconnect task already running")
            return

        self._should_stop = False
        self._reconnect_task = asyncio.create_task(self._auto_reconnect())
        _LOGGER.debug("New reconnect task created")

    async def _auto_reconnect(self) -> None:
        """自动重连循环"""
        _LOGGER.debug(f"_auto_reconnect started for {self._host}:{self._port}")
        while not self._should_stop:
            try:
                await self._attempt_connect()

                # 连接成功则重置重试间隔
                self._current_retry_interval = self._initial_retry_interval
                _LOGGER.info(f"Successfully connected to {self._host}:{self._port}")
                return

            except Exception as err:
                _LOGGER.warning(
                    f"Connection attempt {self._connect_attempts} failed: {err}, "
                    f"retrying in {self._current_retry_interval:.1f}s"
                )

                await asyncio.sleep(self._current_retry_interval)

                # 指数退避增加重试间隔
                self._current_retry_interval = min(
                    self._current_retry_interval * 2, self._max_retry_interval
                )

    async def _attempt_connect(self) -> None:
        """单次连接尝试"""
        _LOGGER.debug(
            f"_attempt_connect to {self._host}:{self._port}, attempt {self._connect_attempts + 1}"
        )
        self._connect_attempts += 1
        self._last_connect_time = time.time()

        key = f"{self._host}_{self._port}"
        TCPClient._debug_stats[key]["connect_attempts"] += 1
        TCPClient._debug_stats[key]["last_activity"] = time.time()

        connection_successful = False
        try:
            # 带超时的连接
            async with asyncio.timeout(self._connection_timeout):
                self._reader, self._writer = await asyncio.open_connection(
                    self._host, self._port
                )

            connection_successful = True
            self._is_connected = True
            _LOGGER.info(f"Connected to {self._host}:{self._port}")

            # 启动数据监听任务
            self._keepalive_task = asyncio.create_task(self._keepalive())

        except asyncio.TimeoutError:
            _LOGGER.error(f"Connection timeout after {self._connection_timeout}s")
            raise ConnectionError(
                f"Connection timeout after {self._connection_timeout}s"
            )
        except Exception as err:
            _LOGGER.error(f"Connection attempt failed: {err}")
            raise err
        finally:
            # 如果连接不成功，确保清理资源
            if not connection_successful:
                self._cleanup_connection()

    async def _keepalive(self) -> None:
        """维持连接并监听数据"""
        _LOGGER.debug(f"_keepalive started for {self._host}:{self._port}")
        key = f"{self._host}_{self._port}"

        try:
            while not self._should_stop and self._is_connected:
                try:
                    if self._reader:
                        data = await self._reader.read(1024)
                        if not data:  # 空数据表示连接关闭
                            _LOGGER.warning("Connection closed by peer (empty data)")
                            raise ConnectionError("Connection closed by peer")

                        self._last_receive_time = time.time()
                        TCPClient._debug_stats[key]["receive_count"] += 1
                        TCPClient._debug_stats[key]["last_activity"] = time.time()

                        _LOGGER.debug(
                            f"Received {len(data)} bytes from {self._host}:{self._port}"
                        )

                        if self._callback:
                            self._callback(data)

                except ConnectionError:
                    _LOGGER.warning("Connection lost")
                    raise
                except Exception as err:
                    _LOGGER.error(f"Data receive error: {err}", exc_info=True)
                    continue

        except asyncio.CancelledError:
            _LOGGER.debug("Keepalive task cancelled")
            raise
        except Exception as err:
            _LOGGER.error(f"Keepalive task error: {err}")
        finally:
            _LOGGER.debug("Keepalive task finished, cleaning up connection")
            self._cleanup_connection()
            if not self._should_stop:
                _LOGGER.info("Attempting to reconnect...")
                # 避免直接递归调用，使用create_task
                asyncio.create_task(self.connect())

    async def send(self, data: bytes) -> bool:
        """发送数据"""
        _LOGGER.debug(
            f"send called for {self._host}:{self._port}, data length: {len(data)}"
        )
        if not self._is_connected or not self._writer:
            _LOGGER.warning("Cannot send data: not connected")
            return False

        try:
            self._writer.write(data)
            await self._writer.drain()
            self._last_send_time = time.time()

            key = f"{self._host}_{self._port}"
            TCPClient._debug_stats[key]["send_count"] += 1
            TCPClient._debug_stats[key]["last_activity"] = time.time()

            _LOGGER.debug(
                f"Successfully sent {len(data)} bytes to {self._host}:{self._port}"
            )
            return True
        except Exception as err:
            _LOGGER.error(f"Send failed: {err}")
            self._cleanup_connection()
            return False

    def set_callback(self, callback: Callable[[bytes], None]) -> None:
        """设置数据接收回调"""
        _LOGGER.debug(f"set_callback for {self._host}:{self._port}")
        self._callback = callback

    def _cleanup_connection(self) -> None:
        """清理连接资源"""
        _LOGGER.debug(f"_cleanup_connection for {self._host}:{self._port}")
        self._is_connected = False

        key = f"{self._host}_{self._port}"
        with TCPClient._lock:
            if key in TCPClient._instances:
                _LOGGER.debug(f"Removing instance from TCPClient._instances for {key}")
                TCPClient._debug_stats[key]["destroyed_count"] += 1
                del TCPClient._instances[key]
            else:
                _LOGGER.debug(f"No instance found for {key}")

        # 取消旧的keepalive任务（如果存在）
        if self._keepalive_task and not self._keepalive_task.done():
            _LOGGER.debug("Cancelling keepalive task")
            self._keepalive_task.cancel()
            self._keepalive_task = None

        if self._writer:
            try:
                _LOGGER.debug("Closing writer")
                self._writer.close()
                asyncio.create_task(self._wait_closed(self._writer))
            except Exception as e:
                _LOGGER.error(f"Error closing writer: {e}")
            finally:
                self._writer = None
                self._reader = None

    async def _wait_closed(self, writer):
        """等待writer关闭"""
        try:
            await writer.wait_closed()
            _LOGGER.debug("Writer closed successfully")
        except Exception as e:
            _LOGGER.debug(f"Writer close completed with: {e}")

    async def disconnect(self) -> None:
        """断开网络连接，但不清理实例资源"""
        _LOGGER.debug(f"disconnect called for {self._host}:{self._port}")
        self._should_stop = True

        # 只清理网络连接相关资源
        self._cleanup_connection()

        # 取消网络相关任务
        await self._cancel_network_tasks()

        _LOGGER.info(f"Disconnected from {self._host}:{self._port}")

    async def _cancel_network_tasks(self) -> None:
        """取消网络相关任务"""
        tasks_to_cancel = []
        if self._keepalive_task:
            tasks_to_cancel.append(("keepalive", self._keepalive_task))
        if self._reconnect_task:
            tasks_to_cancel.append(("reconnect", self._reconnect_task))

        for task_name, task in tasks_to_cancel:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=3.0)
                    _LOGGER.debug(f"{task_name} task cancelled successfully")
                except asyncio.CancelledError:
                    _LOGGER.debug(f"{task_name} task cancelled")
                except asyncio.TimeoutError:
                    _LOGGER.warning(f"{task_name} task cancellation timed out")
                except Exception as e:
                    _LOGGER.error(f"{task_name} task cancellation failed: {e}")

    async def __aenter__(self):
        _LOGGER.debug(f"__aenter__ for {self._host}:{self._port}")
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        _LOGGER.debug(f"__aexit__ for {self._host}:{self._port}")
        await self.disconnect()

    async def enqueue_data(self, message):
        """将数据放入队列中"""
        _LOGGER.debug(
            f"enqueue_data for {self._host}:{self._port}, queue size before: {self._queue.qsize()}"
        )
        await self._queue.put(message)
        _LOGGER.debug(
            f"enqueue_data for {self._host}:{self._port}, queue size after: {self._queue.qsize()}"
        )

    async def _send_loop(self):
        """发送循环任务"""
        _LOGGER.debug(f"_send_loop started for {self._host}:{self._port}")
        self._is_running = True
        key = f"{self._host}_{self._port}"

        try:
            while self._is_running and not self._should_stop:
                try:
                    # 从队列中获取数据（如果队列为空，则等待直到有数据）
                    message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    _LOGGER.debug(f"Sending message: {message}")

                    success = await self.send(message.encode())
                    if not success:
                        _LOGGER.warning("Send failed, will retry later")
                        # 发送失败，将消息重新放回队列
                        await self._queue.put(message)

                    await asyncio.sleep(0.1)  # 短暂延迟避免CPU过度使用
                    self._queue.task_done()

                except asyncio.TimeoutError:
                    # 超时是正常的，用于检查停止条件
                    continue
                except asyncio.CancelledError:
                    _LOGGER.debug("Send loop cancelled")
                    break
                except Exception as e:
                    _LOGGER.error(f"Error in send loop: {e}")
                    await asyncio.sleep(1)  # 出错时等待一段时间再继续

        except Exception as e:
            _LOGGER.error(f"Send loop error: {e}")
        finally:
            _LOGGER.debug("_send_loop finished")
            self._is_running = False

    async def clean(self) -> None:
        """完全清理所有资源（包括实例本身）"""
        _LOGGER.debug(f"clean called for {self._host}:{self._port}")

        # 先断开连接
        await self.disconnect()

        # 清理发送循环任务和队列
        await self._cleanup_send_loop()

        # 从实例字典中移除自己
        self._remove_from_instances()

        _LOGGER.debug(f"Completely cleaned up {self._host}:{self._port}")

    async def _cleanup_send_loop(self) -> None:
        """清理发送循环相关资源"""
        self._is_running = False

        send_loop_task = self._send_loop_task
        if send_loop_task:
            send_loop_task.cancel()
            try:
                await send_loop_task  # type: ignore
                _LOGGER.debug("Send loop task cancelled successfully")
            except asyncio.CancelledError:
                _LOGGER.debug("Send loop task cancelled")
            except Exception as ex:
                _LOGGER.error(f"Send loop task cancellation failed: {ex}")

        # 清空队列
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except:
                break

    def _remove_from_instances(self) -> None:
        """从实例字典中移除自己"""
        key = f"{self._host}_{self._port}"
        with TCPClient._lock:
            if key in TCPClient._instances:
                _LOGGER.debug(f"Removing instance from TCPClient._instances for {key}")
                TCPClient._debug_stats[key]["destroyed_count"] += 1
                del TCPClient._instances[key]

    def get_stats(self):
        """获取当前实例的统计信息"""
        return {
            "host": self._host,
            "port": self._port,
            "is_connected": self._is_connected,
            "connect_attempts": self._connect_attempts,
            "queue_size": self._queue.qsize(),
            "is_running": self._is_running,
            "should_stop": self._should_stop,
            "last_connect_time": self._last_connect_time,
            "last_send_time": self._last_send_time,
            "last_receive_time": self._last_receive_time,
        }


# 调试工具函数
async def monitor_tcp_clients(interval=10):
    """监控所有TCP客户端的状态"""
    while True:
        try:
            debug_info = TCPClient.get_debug_info()
            _LOGGER.info("=== TCP Clients Debug Info ===")
            _LOGGER.info(f"Total instances: {debug_info['total_instances']}")

            for key, info in debug_info["instances_info"].items():
                _LOGGER.info(f"Instance {key}: {info}")

            _LOGGER.info("Debug statistics:")
            for key, stats in debug_info["debug_stats"].items():
                _LOGGER.info(f"  {key}: {stats}")

            _LOGGER.info("==============================")

            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            _LOGGER.error(f"Monitor error: {e}")
            await asyncio.sleep(interval)


# 使用示例
async def demo():
    """演示如何使用TCPClient"""
    # 设置更详细的日志级别
    logging.basicConfig(level=logging.DEBUG)

    # 启动监控任务
    # monitor_task = asyncio.create_task(monitor_tcp_clients(5))

    try:
        # 创建TCP客户端实例
        client = TCPClient.get_instance("192.168.0.111", 8092)

        # 设置接收回调
        def data_callback(data):
            _LOGGER.info(f"Received data: {data}")

        if client:
            client.set_callback(data_callback)

            # 连接并发送数据
            await client.connect()

            # # 发送一些测试数据
            # for i in range(5):
            #     await client.enqueue_data(f"Hello {i}")
            #     await asyncio.sleep(1)

            # 等待一段时间
            await asyncio.sleep(30)

            # 清理
            await client.clean()

    except Exception as e:
        _LOGGER.error(f"Demo error: {e}")
    # finally:
    #     monitor_task.cancel()
    #     try:
    #         await monitor_task
    #     except asyncio.CancelledError:
    #         pass


if __name__ == "__main__":
    asyncio.run(demo())
