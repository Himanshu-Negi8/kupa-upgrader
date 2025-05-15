Installation
============

Quick Install
------------

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/yourusername/kupa.git
    cd kupa

    # Run the install script
    ./install.sh

Manual Installation
----------------

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/yourusername/kupa.git
    cd kupa

    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install the package
    pip install -e .

Development Installation
---------------------

.. code-block:: bash

    # For development with testing tools
    ./install.sh --dev
    # Or manually:
    pip install -e ".[dev]"

Using Docker
-----------

.. code-block:: bash

    # Build the Docker image
    docker build -t kupa .

    # Run the Docker container
    docker run -it kupa --help

Using Docker Compose
------------------

.. code-block:: bash

    # Start the server and related services
    docker-compose up

    # Run in the background
    docker-compose up -d

Environment Variables
-------------------

KuPa requires the following environment variables to be set:

* ``OPENAI_API_KEY``: Your OpenAI API key for AI model integration
* ``GITHUB_TOKEN``: Your GitHub token for creating pull requests

You can set these in your shell:

.. code-block:: bash

    export OPENAI_API_KEY=your_key
    export GITHUB_TOKEN=your_token

Or when running with Docker:

.. code-block:: bash

    docker run -e OPENAI_API_KEY=your_key -e GITHUB_TOKEN=your_token -it kupa ...
