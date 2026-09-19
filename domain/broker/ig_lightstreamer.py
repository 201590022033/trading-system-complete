"""Concrete PRICE-only SDK transport. No order or message-sending interface."""
from datetime import datetime, timezone
from urllib.parse import urlsplit


class LightstreamerTransport:
    def __init__(self, *, on_observation=None, sdk=None):
        if sdk is None:
            import lightstreamer.client as sdk
        self.sdk=sdk
        self.on_observation=on_observation or (lambda value: None)
        self.client=None
        self.connected=False
        self.error=None
        self.subscribed=set()
        self.subscriptions={}
        self.failures=0
        self.rejected_updates=0

    def connect(self, endpoint, account, password):
        url=urlsplit(endpoint)
        if url.scheme!='https' or not url.hostname or not url.hostname.startswith('demo-') or not url.hostname.endswith('.marketdatasystems.com') or url.username or url.password:
            raise ValueError('Expected an IG Demo streaming endpoint')
        if self.client is not None:
            self.disconnect()
        owner=self
        class Listener(self.sdk.ClientListener):
            def onStatusChange(self, status):
                owner.connected=status.startswith('CONNECTED:')
                if status.startswith('DISCONNECTED:'):
                    owner.failures+=1
                    if owner.failures>=3:
                        owner.error='STREAM_RECONNECT_LIMIT'
                        owner.disconnect()
            def onServerError(self, code, message):
                owner.error='STREAM_SERVER_ERROR'
                owner.disconnect()
        self.client=self.sdk.LightstreamerClient(endpoint,None)
        self.client.connectionDetails.setUser(account)
        self.client.connectionDetails.setPassword(password)
        self.client.addListener(Listener())
        self.client.connect()

    def subscribe(self, item, fields, callback):
        if not item.startswith('PRICE:') or self.client is None:
            raise ValueError('Connected PRICE subscription required')
        if item in self.subscriptions:
            return
        owner=self
        class Listener(self.sdk.SubscriptionListener):
            def onSubscription(self): owner.subscribed.add(item)
            def onUnsubscription(self): owner.subscribed.discard(item)
            def onSubscriptionError(self, code, message):
                owner.error='PRICE_SUBSCRIPTION_REJECTED'
                owner.subscribed.discard(item)
            def onItemUpdate(self, update):
                try:
                    values={field:update.getValue(field) for field in fields}
                    observation=callback(values,datetime.now(timezone.utc))
                    owner.on_observation(observation)
                except (ValueError,TypeError,OverflowError):
                    owner.rejected_updates+=1
        subscription=self.sdk.Subscription('MERGE',[item],list(fields))
        subscription.setDataAdapter('Pricing')
        subscription.setRequestedSnapshot('yes')
        subscription.addListener(Listener())
        self.subscriptions[item]=subscription
        self.client.subscribe(subscription)

    def unsubscribe(self, item):
        subscription=self.subscriptions.pop(item,None)
        if subscription is not None and self.client is not None:
            self.client.unsubscribe(subscription)
        self.subscribed.discard(item)

    def disconnect(self):
        if self.client is not None:
            self.client.disconnect()
        self.connected=False
        self.subscribed.clear()
        self.subscriptions.clear()
