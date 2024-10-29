import os
from dotenv import load_dotenv
import os

_sparrow_root = os.getcwd()
_workspace = f"{_sparrow_root}/.workspace"

## Load env vars
load_dotenv()

BASIC_AUTH_ENABLED = os.environ.get("SPARROW_BASIC_AUTH_ENABLED", "false") == "true"
BASIC_AUTH_USERNAME = os.environ.get("SPARROW_BASIC_AUTH_USERNAME", "sparrow")
BASIC_AUTH_PASSWORD = os.environ.get("SPARROW_BASIC_AUTH_PASSWORD", "worraps")

## Path prefix for the server
SPARROW_ROOT_PATH = os.environ.get("SPARROW_ROOT_PATH", "")
SPARROW_CLONE_DIR = os.environ.get("SPARROW_CLONE_DIR", f"{_workspace}/repos")
SPARROW_PLAN_DIR = os.environ.get("SPARROW_PLAN_DIR", f"{_workspace}/plans")
SPARROW_KUBECONFIG_DIR = os.environ.get("SPARROW_KUBECONFIG_DIR", f"{_workspace}/kubeconfigs")

## Access the Version Control Provider
VCS_BASE_URL = os.environ.get("SPARROW_VCS_BASE_URL")
if not VCS_BASE_URL:
    raise ValueError("SPARROW_VCS_BASE_URL is not set")

VCS_TOKEN = os.environ.get("SPARROW_VCS_TOKEN")
if not VCS_BASE_URL:
    raise ValueError("SPARROW_VCS_BASE_URL is not set")

## Allow configuring a path for binary installation
BINARY_PATH = os.environ.get("SPARROW_BINARY_PATH", "/app/bin")

## Configure helm
HELM_VERSION = os.environ.get("SPARROW_HELM_VERSION", "3.15.0")

## Configure Azure
AZURE_SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

DIFF_CONTEXT = os.environ.get("SPARROW_DIFF_CONTEXT", "-1")
