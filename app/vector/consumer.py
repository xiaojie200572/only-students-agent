import json
import asyncio
import threading
from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

from app.config import get_settings
from app.vector.client import VectorStore
from app.vector.embedder import Embedder

settings = get_settings()


class NoteVectorSyncConsumer:
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedder = Embedder()
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self._running = False

    def connect(self):
        credentials = pika.PlainCredentials(settings.rabbitmq_username, settings.rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=300,
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        sync_queue = "note.vector.sync.queue"
        delete_queue = "note.vector.delete.queue"

        for queue in [sync_queue, delete_queue]:
            self.channel.queue_declare(queue=queue, durable=True)

        self.channel.exchange_declare(
            exchange=settings.rabbitmq_exchange, exchange_type="topic", durable=True
        )

        self.channel.queue_bind(
            queue=sync_queue, exchange=settings.rabbitmq_exchange, routing_key="note.vector.sync"
        )
        self.channel.queue_bind(
            queue=delete_queue,
            exchange=settings.rabbitmq_exchange,
            routing_key="note.vector.delete",
        )

        print(f"Connected to RabbitMQ, listening on queues: {sync_queue}, {delete_queue}")

    def process_message(self, ch, method, properties, body):
        routing_key = method.routing_key
        print(f"Received message with routing_key: {routing_key}")

        try:
            if routing_key == "note.vector.delete":
                note_id = json.loads(body)
                if isinstance(note_id, str):
                    note_id = int(note_id)
                print(f"Received note delete message: note_id={note_id}")
                self._delete_note_from_milvus(note_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Note {note_id} deleted from Milvus successfully")
            else:
                note = json.loads(body)
                note_id = note.get("id") or note.get("noteId")
                print(f"Received note sync message: note_id={note_id}")

                asyncio.run(self._sync_note_to_milvus(note))

                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Note {note_id} synced to Milvus successfully")

        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _delete_note_from_milvus(self, note_id: int):
        try:
            existing = self._search_by_note_id(note_id)
            if existing:
                self.vector_store.delete_by_ids([existing["id"]])
                print(f"Deleted note {note_id} from Milvus")
            else:
                print(f"Note {note_id} not found in Milvus")
        except Exception as e:
            print(f"Error deleting note {note_id} from Milvus: {e}")

    async def _sync_note_to_milvus(self, note: dict):
        text = self._prepare_note_text(note)
        embedding = await self.embedder.embed_query(text)

        note_data = {
            "note_id": note.get("id") or note.get("noteId"),
            "title": note.get("title", ""),
            "content": note.get("content", ""),
            "summary": note.get("summary", "") or note.get("content", "")[:500],
            "author_id": note.get("userId") or note.get("authorId") or 0,
            "author_name": note.get("authorNickname") or note.get("authorName", ""),
            "tags": note.get("tags", []),
            "embedding": embedding,
        }

        existing = self._search_by_note_id(note_data["note_id"])
        if existing:
            self.vector_store.delete_by_ids([existing["id"]])
            print(f"Deleted existing note {note_data['note_id']} from Milvus")

        self.vector_store.insert([note_data])

    def _prepare_note_text(self, note: dict) -> str:
        parts = [
            note.get("title", ""),
            note.get("summary", ""),
            note.get("content", ""),
        ]
        tags = note.get("tags", [])
        if tags:
            if isinstance(tags, str):
                tags = tags.split(",")
            parts.append("标签: " + ", ".join(tags))
        return "\n".join(filter(None, parts))

    def _search_by_note_id(self, note_id: int) -> Optional[dict]:
        try:
            from pymilvus import MilvusClient

            client = MilvusClient(uri=settings.milvus_uri)
            results = client.query(
                collection_name=settings.milvus_collection,
                filter=f"note_id == {note_id}",
                output_fields=["id", "note_id"],
            )
            return results[0] if results else None
        except Exception as e:
            print(f"Error searching note_id {note_id}: {e}")
            return None

    def start_consuming(self):
        self._running = True
        self.connect()

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue="note.vector.sync.queue",
            on_message_callback=self.process_message,
        )
        self.channel.basic_consume(
            queue="note.vector.delete.queue",
            on_message_callback=self.process_message,
        )

        print("Starting to consume messages...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()

    def stop_consuming(self):
        self._running = False
        if self.channel:
            self.channel.stop_consuming()
        if self.connection:
            self.connection.close()
        print("RabbitMQ consumer stopped")


def run_consumer():
    consumer = NoteVectorSyncConsumer()
    consumer.start_consuming()


def start_rabbitmq_consumer():
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()
    print("RabbitMQ consumer thread started")


if __name__ == "__main__":
    run_consumer()
