"""
Dependencies and Requirements for Multi-Dataset Training System

This file lists all the dependencies you need and verifies they're installed.
"""

# Core imports used by the training system
CORE_IMPORTS = [
    "csv",
    "json",
    "pickle",
    "pathlib",
    "typing",
    "logging",
    "collections",
    "statistics",
    "datetime",
]

# Optional imports that enable enhanced features
OPTIONAL_IMPORTS = {
    "numpy": {
        "purpose": "For semantic search (if enabled)",
        "install": "pip install numpy",
        "required": False,
    },
    "sklearn": {
        "purpose": "For advanced ML features (future enhancement)",
        "install": "pip install scikit-learn",
        "required": False,
    },
    "pandas": {
        "purpose": "For better data handling",
        "install": "pip install pandas",
        "required": False,
    },
}

# System compatibility
COMPATIBILITY = {
    "python_version": "3.9+",
    "os": ["Windows", "macOS", "Linux"],
    "memory_minimum": "2GB (4GB+ recommended)",
    "disk_space": "500MB for datasets and models",
}


def check_core_imports():
    """Verify all core imports are available."""
    print("✓ Checking core imports...")
    missing = []
    
    for imp in CORE_IMPORTS:
        try:
            __import__(imp)
            print(f"  ✅ {imp}")
        except ImportError:
            print(f"  ❌ {imp} - NOT AVAILABLE")
            missing.append(imp)
    
    if missing:
        print(f"\n⚠️ Missing core imports: {', '.join(missing)}")
        print("These should be available in Python 3.9+")
        return False
    
    print("✅ All core imports available!\n")
    return True


def check_optional_imports():
    """Check optional imports and suggest installation if missing."""
    print("✓ Checking optional imports...")
    
    for module, info in OPTIONAL_IMPORTS.items():
        try:
            __import__(module)
            print(f"  ✅ {module} - {info['purpose']}")
        except ImportError:
            status = "⚠️" if info['required'] else "ℹ️"
            print(f"  {status} {module} - NOT INSTALLED (optional)")
            print(f"     Purpose: {info['purpose']}")
            print(f"     Install: {info['install']}")
    
    print()


def check_system_requirements():
    """Check system requirements."""
    print("✓ System Requirements:")
    print(f"  Python: {COMPATIBILITY['python_version']}")
    print(f"  Memory: {COMPATIBILITY['memory_minimum']}")
    print(f"  Disk: {COMPATIBILITY['disk_space']}")
    print(f"  OS: {', '.join(COMPATIBILITY['os'])}")
    print()


def verify_structure():
    """Verify expected directory structure."""
    import os
    
    print("✓ Verifying directory structure...")
    
    required_dirs = [
        "ai_backend",
        "ai_backend/datasets",
        "ai_backend/logs",
    ]
    
    required_files = [
        "ai_backend/multi_dataset_loader.py",
        "ai_backend/training_engine.py",
        "ai_backend/personalization_engine.py",
        "ai_backend/enhanced_recommendation_engine.py",
        "ai_backend/dataset_context_builder.py",
        "ai_backend/training_pipeline.py",
        "ai_backend/coach_agent_integration.py",
    ]
    
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - NOT FOUND")
    
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
    
    print()


def check_datasets():
    """Check if datasets are available."""
    from pathlib import Path
    
    print("✓ Checking datasets...")
    
    dataset_dir = Path("ai_backend/datasets")
    
    if not dataset_dir.exists():
        print(f"  ❌ Dataset directory not found: {dataset_dir}")
        return 0
    
    csv_files = list(dataset_dir.glob("*.csv"))
    xlsx_files = list(dataset_dir.glob("*.xlsx"))
    
    total = len(csv_files) + len(xlsx_files)
    
    print(f"  ✅ Found {total} dataset files")
    print(f"     CSV files: {len(csv_files)}")
    print(f"     XLSX files: {len(xlsx_files)}")
    
    if total < 30:
        print(f"  ⚠️ Expected 50+, found {total}")
    
    print()
    return total


def quick_import_test():
    """Test that can import the training system."""
    print("✓ Testing imports...")
    
    try:
        print("  Importing multi_dataset_loader...")
        from ai_backend.multi_dataset_loader import MultiDatasetLoader
        print("  ✅ OK")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    try:
        print("  Importing training_engine...")
        from ai_backend.training_engine import TrainingEngine
        print("  ✅ OK")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    try:
        print("  Importing personalization_engine...")
        from ai_backend.personalization_engine import PersonalizationEngine
        print("  ✅ OK")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    try:
        print("  Importing enhanced_recommendation_engine...")
        from ai_backend.enhanced_recommendation_engine import EnhancedRecommendationEngine
        print("  ✅ OK")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    try:
        print("  Importing dataset_context_builder...")
        from ai_backend.dataset_context_builder import DatasetContextBuilder
        print("  ✅ OK")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    try:
        print("  Importing training_pipeline...")
        from ai_backend.training_pipeline import TrainingPipeline
        print("  ✅ OK")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False
    
    print()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Dataset Training System - Requirements Verification")
    print("=" * 60)
    print()
    
    # Run all checks
    check_system_requirements()
    check_core_imports()
    check_optional_imports()
    verify_structure()
    dataset_count = check_datasets()
    quick_import_test()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if dataset_count >= 30:
        print("✅ System ready to use!")
        print("\nNext steps:")
        print("  1. python ai_backend/training_pipeline.py")
        print("  2. from training_pipeline import TrainingPipeline")
        print("  3. pipeline = TrainingPipeline(...)")
        print("  4. pipeline.train()")
    else:
        print(f"⚠️ Found {dataset_count} datasets, expected 50+")
        print("Make sure all datasets are in ai_backend/datasets/")
    
    print("\nFor more info:")
    print("  - See QUICKSTART.md for quick start guide")
    print("  - See MULTI_DATASET_TRAINING_GUIDE.md for full guide")
    print("  - See IMPLEMENTATION_SUMMARY.md for architecture details")
    print()
