starter-java-web
================

This Starter Kit provides the basic building blocks for deploying, updating and scaling Java-based applications on Qubell Platform, and can be used as a starting point for your own automation project.

Features
--------

 - Launching a new sandbox instance of a web application
 - Updating an existing live application to a new version of the source code and/or database schema
 - Scaling the web tier up and down

Configurations
--------------
[![Build Status](https://travis-ci.org/qubell-bazaar/component-petclinic.png?branch=master)](https://travis-ci.org/qubell-bazaar/starter-java-web)

 - [Tomcat 5](https://github.com/qubell-bazaar/component-tomcat-dev), [MySQL 5](https://github.com/qubell-bazaar/component-mysql-dev), [HAProxy 1.4](https://github.com/qubell-bazaar/component-haproxy), CentOS 6.4 (us-east-1/ami-eb6b0182), AWS EC2 m1.small, root

Pre-requisites
--------------
 - Configured Cloud Account a in chosen environment
 - Either installed Chef on target compute OR launch under root
 - All pre-requisites from the components above
