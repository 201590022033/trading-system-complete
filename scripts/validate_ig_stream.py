"""Bounded DEMO price subscription check; never constructs an order."""
import argparse
from dataclasses import asdict
from datetime import datetime
import json
import os
import sys
from threading import Event
from domain.broker.ig import IGConfig, IGReadOnlyAdapter, IGMapping, IGRequestError
from domain.broker.ig_streaming import IGMarketStream
from domain.broker.ig_lightstreamer import LightstreamerTransport


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials-stdin',action='store_true')
    parser.add_argument('--seconds',type=int,default=20,choices=range(1,46))
    args=parser.parse_args()
    config=IGConfig.from_env(json.load(sys.stdin) if args.credentials_stdin else os.environ)
    if config.environment!='DEMO':
        raise ValueError('DEMO required before any network request')
    stream=None
    received=Event()
    observations=[]
    def accept(value):
        if len(observations)<5: observations.append(value)
        received.set()
    try:
        adapter=IGReadOnlyAdapter(config)
        adapter.authenticate()
        market=adapter.get_market('CC.D.LCO.BMU.IP')
        mapping=IGMapping('BRENT','IG',market.epic,'DEMO',market.instrument_type,market.name)
        transport=LightstreamerTransport(on_observation=accept)
        stream=IGMarketStream(adapter,[mapping],transport=transport)
        stream.connect()
        received.wait(args.seconds)
        print(json.dumps({'environment':'DEMO','market_status':market.market_status,
            'health':asdict(stream.health()),'subscription_acknowledged':bool(transport.subscribed),
            'observations':[asdict(x) for x in observations],
            'rejected_updates':transport.rejected_updates,'orders_submitted':0},
            default=lambda x:x.isoformat() if isinstance(x,datetime) else str(x)))
    except IGRequestError as exc:
        print(json.dumps({**exc.diagnostic('DEMO'),'orders_submitted':0}))
    except Exception as exc:
        print(json.dumps({'state':'STREAM_CHECK_FAILED','error_type':type(exc).__name__,'orders_submitted':0}))
    finally:
        if stream is not None: stream.disconnect()


if __name__=='__main__': main()
