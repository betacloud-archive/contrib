=======
Contrib
=======

Usage
=====

.. code::

   $ virtualenv .venv
   $ source .venv/bin/activate
   $ pip install -r requirements.txt

clouds.yml
==========

`shade <https://github.com/openstack-infra/shade>`_ is a simple client library for interacting with OpenStack clouds. shade uses
`os-client-config <https://github.com/openstack/os-client-config>`_, a unified config handling for client libraries, for the
cloud configuration.

This is an example ``clouds.yaml`` configuration file for Betacloud::

   ---
   clouds:
     betacloud:
       auth:
         username: YOUR_USERNAME
         password: YOUR_PASSWORD
         project_name: YOUR_PROJECTNAME
         auth_url: https://api-1.betacloud.io:5000/v3
         project_domain_name: default
         user_domain_name: default
       identity_api_version: 3
