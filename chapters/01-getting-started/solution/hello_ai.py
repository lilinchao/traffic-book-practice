import argparse


def build_message(topic: str) -> str:
    return f"Hello, {topic}. Keep the experiment reproducible."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="AI engineering practice")
    args = parser.parse_args()
    print(build_message(args.topic))


if __name__ == "__main__":
    main()
