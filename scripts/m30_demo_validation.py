"""M30 safe command boundary; defaults to non-mutating authorization status."""
import argparse,json
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--authorize-external-demo-order",action="store_true");args=parser.parse_args()
    if args.authorize_external_demo_order:parser.error("Phase B requires a separately constructed factual validation plan; this status command never submits")
    print(json.dumps({"phase":"A","outcome":"NOT_AUTHORIZED","external_mutation":"NOT PERFORMED","next":"construct controlled factual DemoValidationPlan"},sort_keys=True))
if __name__=="__main__":main()
