=======
Contrib
=======

.. image:: https://travis-ci.org/betacloud/contrib.svg?branch=master
    :target: https://travis-ci.org/betacloud/contrib

Usage
=====

.. code::

   $ virtualenv .venv
   $ source .venv/bin/activate
   $ pip install -r requirements.txt

Shade
=====

`shade <https://github.com/openstack-infra/shade>`_ is a simple client library for interacting with OpenStack clouds.

shade uses `os-client-config <https://github.com/openstack/os-client-config>`_, a unified config handling for client libraries, for the cloud configuration.

This is an example ``clouds.yaml`` configuration file for Betacloud with region ``de-1``::

   ---
   clouds:
     betacloud:
       auth:
         username: YOUR_USERNAME
         password: YOUR_PASSWORD
         project_name: YOUR_PROJECTNAME
         auth_url: https://de-1.betacloud.io:5000/v3
         project_domain_name: YOUR_DOMAINNAME
         user_domain_name: YOUR_DOMAINNAME
       identity_api_version: 3

``YOUR_DOMAINNAME`` is ``default`` by default.

Tools using the shade library are located in the ``shade`` directory.

instance-spawner.py
-------------------

Script to demonstrate the use of the shade library. It will spawn a specific number of instances and will assign a floating IP address when the parameter ``--floating`` is set.

.. code::

   $ python shade/instance-spawner.py --cloud betacloud start --prefix foobar --flavor t2.micro.1 --image "Ubuntu 16.04 (Xenial Xerus)" --key berendt --network testing_default_network --number 2 --floating
   2016-07-27 15:08:33.847 4183 INFO instance-spawner [-] spawning instance foobar-plfmer (1 of 2)
   2016-07-27 15:09:08.676 4183 INFO instance-spawner [-] spawning instance foobar-froqyz (2 of 2)

glance-share-image.py
---------------------

The ``glance member-*`` commands are only usable with IDs. This is a little bit uncomfortable. With ``glance-share-image.py`` it is possible to share an image using the names of projects and images.

.. code::

   $ python shade/glance-share-image.py --cloud betacloud --target testing_project001 --image "Some private image"
