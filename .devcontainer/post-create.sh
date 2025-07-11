#!/bin/bash
#loading functions to script
export SECONDS=0
source /workspaces/$RepositoryName/.devcontainer/util/functions.sh


bindFunctionsInShell

setupAliases

startKindCluster

installK9s

#TODO: BeforeGoLive: uncomment this. This is only needed for professors to have the Mkdocs live in the container
#installMkdocs

# Dynatrace Credentials are read and saved as a configmap for ease of use
#dynatraceEvalReadSaveCredentials

# Dynatrace Operator can be deployed automatically
#dynatraceDeployOperator

# You can deploy CNFS or AppOnly
#deployCloudNative
#deployApplicationMonitoring

# In here you deploy the Application you want
# The TODO App will be deployed as a sample
#deployTodoApp
deployAITravelAdvisorApp

# The Astroshop keeping changes of demo.live needs certmanagerdocker
#certmanagerInstall
#certmanagerEnable
#deployAstroshop

# If you want to deploy your own App, just create a function in the functions.sh file and call it here.
# deployMyCustomApp

# If the Codespace was created via Workflow end2end test will be done, otherwise
# it'll verify if there are error in the logs and will show them in the greeting as well a monitoring 
# notification will be sent on the instantiation details
finalizePostCreation

printInfoSection "Your dev container finished creating"
