Introduction
============

What is KuPa?
------------

KuPa (Kubernetes Upgrade Path Analyzer) is a tool designed to help Kubernetes users identify
and fix breaking changes in their Kubernetes YAML manifests when upgrading to a newer Kubernetes version.

The Problem
----------

Kubernetes is rapidly evolving, and with each new version, there are API changes, deprecations,
and removals. When upgrading a Kubernetes cluster, it's critical to ensure that all your
deployed resources are compatible with the new version. Manual checking can be tedious and error-prone.

How KuPa Helps
-------------

KuPa automates the process of:

1. Scanning your Kubernetes YAML files for deprecated or removed APIs
2. Identifying breaking changes when upgrading to a specific version
3. Suggesting fixes based on the official Kubernetes documentation
4. Creating new versions of your files with the necessary changes
5. For GitHub repositories, creating pull requests with the fixes

KuPa uses a combination of AI models and official Kubernetes documentation to provide accurate
and helpful suggestions for fixing breaking changes.
