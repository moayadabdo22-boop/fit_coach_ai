from __future__ import annotations

import argparse

from .foods import load_usda_foods
from .exercises import load_exercises


def main():
    parser = argparse.ArgumentParser(description="ETL loader for AI Fitness Coach datasets.")
    parser.add_argument("--foods", action="store_true", help="Load USDA foods")
    parser.add_argument("--exercises", action="store_true", help="Load exercise datasets")
    parser.add_argument("--limit", type=int, default=5000, help="Max rows to load from each dataset")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch insert size")
    parser.add_argument("--include-food-nutrients", action="store_true", help="Load food nutrients table (slower)")
    args = parser.parse_args()

    if args.foods:
        result = load_usda_foods(limit=args.limit, batch_size=args.batch_size, include_food_nutrients=args.include_food_nutrients)
        print("Foods ETL:", result)
    if args.exercises:
        result = load_exercises(limit=args.limit, batch_size=args.batch_size)
        print("Exercises ETL:", result)

    if not args.foods and not args.exercises:
        parser.print_help()


if __name__ == "__main__":
    main()

