#!/bin/bash
# Load framework
source .devcontainer/util/source_framework.sh

# Load tests
source $REPO_PATH/.devcontainer/test/test_functions.sh

printInfoSection "Running integration Tests for the Enablement Framework"

#assertRunningPod dynatrace operator

#assertRunningPod dynatrace activegate

#assertRunningPod dynatrace oneagent

assertRunningPod ai-travel-advisor ollama

assertRunningPod ai-travel-advisor weaviate

assertRunningPod ai-travel-advisor ai-travel-advisor

assertRunningApp 30100
