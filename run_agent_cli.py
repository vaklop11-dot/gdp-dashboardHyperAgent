#!/usr/bin/env python3
import argparse
from pipeline import HyperAgent


def main():
    parser = argparse.ArgumentParser(description='Run HyperAgent from CLI')
    parser.add_argument('task', nargs='+', help='Task description to run')
    args = parser.parse_args()
    task = ' '.join(args.task)

    agent = HyperAgent()
    result = agent.solve(task)
    print('Verdict:', result.verdict)
    print('Iterations:', result.iterations)
    print('Duration (s):', result.duration_sec)
    print('\nFinal output:\n')
    print(result.final_output)


if __name__ == '__main__':
    main()
