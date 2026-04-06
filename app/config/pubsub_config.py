from google.cloud import pubsub_v1

# Shared Pub/Sub publisher client, similar to `new PubSub()` in TS.
pubsub_publisher = pubsub_v1.PublisherClient()