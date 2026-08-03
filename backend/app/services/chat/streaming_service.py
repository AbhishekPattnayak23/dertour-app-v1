import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, AsyncGenerator, Set
from dataclasses import dataclass
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class StreamingConnection:
    id: str
    created_at: float
    last_activity: float
    is_active: bool = True


class SSEManager:
    def __init__(self, heartbeat_interval: int = 30, connection_timeout: int = 300):
        self._connections: Dict[str, StreamingConnection] = {}
        self._connection_queues: Dict[str, asyncio.Queue] = {}
        self._heartbeat_interval = heartbeat_interval
        self._connection_timeout = connection_timeout
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the SSE manager and background tasks"""
        if self._running:
            return
            
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("SSE Manager started")

    async def stop(self):
        """Stop the SSE manager and cleanup resources"""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
                
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        await self._cleanup_all_connections()
        logger.info("SSE Manager stopped")

    def create_connection(self) -> str:
        """Create a new SSE connection and return connection ID"""
        connection_id = str(uuid.uuid4())
        current_time = time.time()
        
        connection = StreamingConnection(
            id=connection_id,
            created_at=current_time,
            last_activity=current_time
        )
        
        self._connections[connection_id] = connection
        self._connection_queues[connection_id] = asyncio.Queue()
        
        logger.info(f"Created SSE connection: {connection_id}")
        return connection_id

    async def remove_connection(self, connection_id: str):
        """Remove an SSE connection"""
        if connection_id in self._connections:
            self._connections[connection_id].is_active = False
            
            # Clear the queue
            if connection_id in self._connection_queues:
                queue = self._connection_queues[connection_id]
                try:
                    while not queue.empty():
                        queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                del self._connection_queues[connection_id]
            
            del self._connections[connection_id]
            logger.info(f"Removed SSE connection: {connection_id}")

    async def send_message(self, connection_id: str, event_type: str, data: Dict):
        """Send a message to a specific connection"""
        if connection_id not in self._connections:
            logger.warning(f"Connection not found: {connection_id}")
            return False
            
        if not self._connections[connection_id].is_active:
            logger.warning(f"Connection inactive: {connection_id}")
            return False
            
        message = {
            'event': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        try:
            await self._connection_queues[connection_id].put(message)
            self._connections[connection_id].last_activity = time.time()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            return False

    async def stream_connection(self, connection_id: str) -> AsyncGenerator[str, None]:
        """Stream messages for a specific connection"""
        if connection_id not in self._connections:
            logger.warning(f"Stream requested for non-existent connection: {connection_id}")
            return
            
        connection = self._connections[connection_id]
        queue = self._connection_queues[connection_id]
        
        try:
            while connection.is_active and self._running:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    sse_data = self._format_sse_message(message)
                    yield sse_data
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error streaming to {connection_id}: {e}")
                    break
                    
        finally:
            await self.remove_connection(connection_id)

    def _format_sse_message(self, message: Dict) -> str:
        """Format message as SSE data"""
        event_type = message.get('event', 'message')
        data = json.dumps(message.get('data', {}))
        
        sse_message = f"event: {event_type}\n"
        sse_message += f"data: {data}\n\n"
        
        return sse_message

    async def _heartbeat_loop(self):
        """Send heartbeat messages to all active connections"""
        while self._running:
            try:
                current_time = time.time()
                heartbeat_data = {'type': 'heartbeat', 'timestamp': current_time}
                
                for connection_id in list(self._connections.keys()):
                    await self.send_message(connection_id, 'heartbeat', heartbeat_data)
                
                await asyncio.sleep(self._heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)

    async def _cleanup_loop(self):
        """Cleanup inactive connections"""
        while self._running:
            try:
                current_time = time.time()
                expired_connections = []
                
                for connection_id, connection in self._connections.items():
                    if (current_time - connection.last_activity) > self._connection_timeout:
                        expired_connections.append(connection_id)
                
                for connection_id in expired_connections:
                    logger.info(f"Cleaning up expired connection: {connection_id}")
                    await self.remove_connection(connection_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(30)

    async def _cleanup_all_connections(self):
        """Cleanup all connections on shutdown"""
        connection_ids = list(self._connections.keys())
        for connection_id in connection_ids:
            await self.remove_connection(connection_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len([c for c in self._connections.values() if c.is_active])

    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """Get information about a specific connection"""
        if connection_id not in self._connections:
            return None
            
        connection = self._connections[connection_id]
        return {
            'id': connection.id,
            'created_at': connection.created_at,
            'last_activity': connection.last_activity,
            'is_active': connection.is_active,
            'age_seconds': time.time() - connection.created_at
        }


class StreamingService:
    def __init__(self, sse_manager: Optional[SSEManager] = None):
        self.sse_manager = sse_manager or SSEManager()
        self._active_streams: Set[str] = set()

    @asynccontextmanager
    async def create_stream(self, stream_id: Optional[str] = None):
        """Create a new streaming context"""
        if stream_id is None:
            stream_id = self.sse_manager.create_connection()
        
        self._active_streams.add(stream_id)
        
        try:
            yield stream_id
        finally:
            self._active_streams.discard(stream_id)
            await self.sse_manager.remove_connection(stream_id)

    async def start_ai_response_stream(self, connection_id: str, prompt: str, model_params: Dict = None):
        """Start streaming an AI response"""
        if model_params is None:
            model_params = {}
            
        await self.sse_manager.send_message(
            connection_id,
            'stream_start',
            {
                'type': 'ai_response',
                'prompt': prompt,
                'model_params': model_params
            }
        )

    async def stream_token(self, connection_id: str, token: str, token_index: int = 0):
        """Stream a single token"""
        await self.sse_manager.send_message(
            connection_id,
            'token',
            {
                'token': token,
                'index': token_index
            }
        )

    async def stream_chunk(self, connection_id: str, chunk: str, chunk_index: int = 0):
        """Stream a text chunk"""
        await self.sse_manager.send_message(
            connection_id,
            'chunk',
            {
                'chunk': chunk,
                'index': chunk_index
            }
        )

    async def stream_error(self, connection_id: str, error_message: str, error_type: str = 'general'):
        """Stream an error message"""
        await self.sse_manager.send_message(
            connection_id,
            'error',
            {
                'message': error_message,
                'type': error_type,
                'timestamp': time.time()
            }
        )

    async def stream_complete(self, connection_id: str, final_response: str = None):
        """Mark stream as complete"""
        data = {
            'status': 'complete',
            'timestamp': time.time()
        }
        
        if final_response:
            data['final_response'] = final_response
            
        await self.sse_manager.send_message(
            connection_id,
            'stream_complete',
            data
        )

    async def stream_metadata(self, connection_id: str, metadata: Dict):
        """Stream metadata information"""
        await self.sse_manager.send_message(
            connection_id,
            'metadata',
            metadata
        )

    async def stream_status(self, connection_id: str, status: str, details: Dict = None):
        """Stream status update"""
        data = {
            'status': status,
            'timestamp': time.time()
        }
        
        if details:
            data.update(details)
            
        await self.sse_manager.send_message(
            connection_id,
            'status',
            data
        )

    def get_stream_generator(self, connection_id: str):
        """Get the SSE stream generator for a connection"""
        return self.sse_manager.stream_connection(connection_id)

    def is_stream_active(self, stream_id: str) -> bool:
        """Check if a stream is currently active"""
        return stream_id in self._active_streams

    def get_active_stream_count(self) -> int:
        """Get the number of active streams"""
        return len(self._active_streams)

    async def cleanup_stream(self, stream_id: str):
        """Manually cleanup a specific stream"""
        if stream_id in self._active_streams:
            self._active_streams.discard(stream_id)
        await self.sse_manager.remove_connection(stream_id)