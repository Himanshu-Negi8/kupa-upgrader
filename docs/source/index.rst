.. KuPa documentation master file

Welcome to KuPa's Documentation
===============================

KuPa (Kubernetes Upgrade Path Analyzer) is a tool for detecting breaking changes
in Kubernetes YAML resources when upgrading to a newer Kubernetes version.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   installation
   usage
   api
   architecture
   contributing
   changelog

Features
--------

* Scan local directories for Kubernetes YAML resources
* Clone and analyze GitHub repositories
* Create pull requests with fixes for GitHub repositories
* Output updated files with timestamps for local directories
* Use AI models to detect breaking changes with fallback to official Kubernetes docs
* Run as a CLI tool or API server

Indices and tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
