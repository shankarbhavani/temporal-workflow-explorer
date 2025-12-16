#!/usr/bin/env python
"""
Test script for YAML-based workflow implementation.
This validates that all components are properly set up.
"""
import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("1. Testing imports...")

    try:
        import yaml
        print("   ✓ PyYAML imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import PyYAML: {e}")
        return False

    try:
        from app.temporal.dsl_workflow import DSLWorkflow, DSLInput
        print("   ✓ DSL workflow imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import DSL workflow: {e}")
        return False

    try:
        from app.temporal.dsl_loader import (
            load_workflow_definition,
            get_default_workflow_path
        )
        print("   ✓ DSL loader imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import DSL loader: {e}")
        return False

    try:
        from app.temporal.activities import sleep_activity
        print("   ✓ Sleep activity imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import sleep activity: {e}")
        return False

    return True


def test_yaml_file():
    """Test that the YAML workflow file exists and is valid."""
    print("\n2. Testing YAML workflow file...")

    yaml_path = Path("app/temporal/load_processing_workflow.yaml")

    if not yaml_path.exists():
        print(f"   ✗ YAML file not found: {yaml_path}")
        return False

    print(f"   ✓ YAML file exists: {yaml_path}")

    try:
        import yaml
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Validate structure
        if "root" not in data:
            print("   ✗ YAML missing 'root' key")
            return False

        if "variables" not in data:
            print("   ✗ YAML missing 'variables' key")
            return False

        print(f"   ✓ YAML structure valid")
        print(f"   ✓ Variables: {list(data['variables'].keys())}")

        # Count steps
        if "sequence" in data["root"]:
            num_steps = len(data["root"]["sequence"]["elements"])
            print(f"   ✓ Number of workflow steps: {num_steps}")

        return True

    except Exception as e:
        print(f"   ✗ Failed to parse YAML: {e}")
        return False


def test_dsl_loader():
    """Test that the DSL loader can parse the YAML file."""
    print("\n3. Testing DSL loader...")

    try:
        from app.temporal.dsl_loader import (
            load_workflow_definition,
            get_default_workflow_path
        )

        yaml_path = get_default_workflow_path("load_processing_workflow")
        print(f"   ✓ Resolved YAML path: {yaml_path}")

        workflow_input = load_workflow_definition(yaml_path)
        print(f"   ✓ YAML loaded successfully")
        print(f"   ✓ Workflow input type: {type(workflow_input).__name__}")

        # Check variables
        variables = workflow_input.variables
        print(f"   ✓ Variables loaded: {list(variables.keys())}")

        # Check root statement
        root_type = type(workflow_input.root).__name__
        print(f"   ✓ Root statement type: {root_type}")

        # Check sequence elements
        if hasattr(workflow_input.root, "sequence"):
            elements = workflow_input.root.sequence.elements
            print(f"   ✓ Number of elements: {len(elements)}")

            # List all activities
            print("   ✓ Activities in sequence:")
            for i, elem in enumerate(elements, 1):
                if hasattr(elem, "activity"):
                    activity_name = elem.activity.name
                    result_var = elem.activity.result
                    print(f"      {i}. {activity_name} -> {result_var}")

        return True

    except Exception as e:
        print(f"   ✗ DSL loader failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_worker_registration():
    """Test that worker has DSL workflow registered."""
    print("\n4. Testing worker configuration...")

    try:
        from app.temporal.worker import run_worker
        print("   ✓ Worker module imported successfully")

        # Check imports in worker
        from app.temporal.workflows import LoadProcessingWorkflow
        from app.temporal.dsl_workflow import DSLWorkflow
        print("   ✓ Both LoadProcessingWorkflow and DSLWorkflow available")

        from app.temporal.activities import (
            send_email_activity,
            load_search_activity,
            process_email_activity,
            extract_data_activity,
            update_load_activity,
            sleep_activity,
        )
        print("   ✓ All activities available (including sleep_activity)")

        return True

    except Exception as e:
        print(f"   ✗ Worker configuration issue: {e}")
        return False


def test_api_endpoint():
    """Test that API endpoint exists."""
    print("\n5. Testing API endpoint...")

    try:
        from app.controllers.workflow_controller import router
        print("   ✓ Workflow controller imported successfully")

        # Check routes
        routes = [route.path for route in router.routes]

        code_based_route = "/load-processing-pipeline"
        yaml_based_route = "/load-processing-pipeline-yaml"

        if code_based_route in routes:
            print(f"   ✓ Code-based endpoint exists: {code_based_route}")
        else:
            print(f"   ✗ Code-based endpoint missing: {code_based_route}")

        if yaml_based_route in routes:
            print(f"   ✓ YAML-based endpoint exists: {yaml_based_route}")
        else:
            print(f"   ✗ YAML-based endpoint missing: {yaml_based_route}")
            return False

        return True

    except Exception as e:
        print(f"   ✗ API endpoint check failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("YAML Workflow Implementation Test")
    print("=" * 60)

    tests = [
        test_imports,
        test_yaml_file,
        test_dsl_loader,
        test_worker_registration,
        test_api_endpoint,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n   ✗ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if all(results):
        print("\n✅ All tests passed! YAML workflow implementation is ready.")
        print("\nNext steps:")
        print("1. Start the Temporal worker: python run_worker.py")
        print("2. Start the FastAPI server: python main.py")
        print("3. Test the YAML workflow:")
        print("   curl -X POST http://localhost:8000/api/v1/workflows/load-processing-pipeline-yaml")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
