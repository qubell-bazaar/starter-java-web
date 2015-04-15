starter-java-web
================

This Starter Kit provides the basic building blocks for deploying, updating and scaling Java-based applications on Qubell Platform, and can be used as a starting point for your own automation project.

Version 2.0-39p
-------------

[![Install](https://raw.github.com/qubell-bazaar/component-skeleton/master/img/install.png)](https://express.qubell.com/applications/upload?metadataUrl=https://raw.github.com/qubell-bazaar/starter-java-web/2.0-39p/meta.yml)

Features
--------

 - Launching a new sandbox instance of a web application
 - Updating an existing live application to a new version of the source code and/or database schema
 - Scaling the web tier up and down

Configurations
--------------
 - [Tomcat 5](https://github.com/qubell-bazaar/component-tomcat-dev), [MySQL 5](https://github.com/qubell-bazaar/component-mysql-dev), [HAProxy 1.4](https://github.com/qubell-bazaar/component-haproxy), CentOS 6.4 (us-east-1/ami-eb6b0182), AWS EC2 m1.small, root

Pre-requisites
--------------
 - Configured Cloud Account a in chosen environment
 - Either installed Chef on target compute OR launch under root
 - All pre-requisites from the components above
