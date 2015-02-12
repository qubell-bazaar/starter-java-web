#!/bin/bash

REPO_SLUG=$(echo ${GIT_URL} | awk -F':' '{print $2;}'|sed '$s/\(.\{4\}\)$//')
REPO_NAME=$(echo ${REPO_SLUG} | cut -d/ -f2)
OWNER_NAME=$(echo ${REPO_SLUG} | cut -d/ -f1)
GIT_REVISION=$(git log --pretty=format:'%h' -n 1)
LAST_COMMIT_AUTHOR=$(git log --pretty=format:'%an' -n1)
BRANCH_NAME=$(echo $GIT_BRANCH|sed -e 's/origin\///g')
COMMIT_MESSAGE=$(git log --format=%B -n1)
VERSION=$(echo $COMMIT_MESSAGE|grep -o 'version:.*'|cut -d: -f2|sed -e 's/^[ \t]*//g;s/[ \t].*$//g')

function check {
    "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo "error run $@"
        exit $status
    fi
    return $status
}

function berks_install {
    local INSTALL_PATH=$1

    berks -d
    berks install -p ${INSTALL_PATH}
}

function package {
    local REVISION=$1

    berks_install berks/cookbooks
    cd berks

    tar -czf ${REPO_NAME}-cookbooks-${REVISION}.tar.gz cookbooks

    cd ../
    mv berks/${REPO_NAME}-cookbooks-${REVISION}.tar.gz ${REPO_NAME}-cookbooks-${REVISION}.tar.gz
}

function publish {
    local REVISION=$1

    package $REVISION

    travis-artifacts upload --path ${REPO_NAME}-cookbooks-${REVISION}.tar.gz --target-path ${OWNER_NAME}/
}

function replace {
    local REVISION=$1

    check sed -i.bak -e 's/'${REPO_NAME}'-cookbooks-stable-[[:alnum:]]*.tar.gz/'${REPO_NAME}'-cookbooks-'${REVISION}'.tar.gz/g' ${REPO_NAME}.yml
    cat ${REPO_NAME}.yml
}

function update_version {
    check sed  -i.bak -e 's/^Version.*$/Version '${VERSION}'/g;s/'${REPO_NAME}'\/.*\/meta.yml/'${REPO_NAME}'\/'${VERSION}'\/meta.yml/g' README.md
    check sed  -i.bak -e 's/'${REPO_NAME}'\/.*\/'${REPO_NAME}'.yml/'${REPO_NAME}'\/'${VERSION}'\/'${REPO_NAME}'.yml/g' meta.yml
}


function publish_github {
    GIT_URL=$(git config remote.origin.url)
    NEW_GIT_URL=$(echo $GIT_URL | sed -e 's/^git:/https:/g' | sed -e 's/^https:\/\//https:\/\/'${GH_TOKEN}':@/')

    git remote rm origin
    git remote add origin ${NEW_GIT_URL}
    git fetch -q
    git config user.name ${GIT_NAME}
    git config user.email ${GIT_EMAIL}
    rm -rf *.tar.gz
    git commit -a -m "CI: Success build ${BUILD_NUMBER} [ci skip]"
    git checkout -b build
  if [[ ! -z $VERSION ]]; then
    git tag | grep ${VERSION}
    RET=$?
  if [[ $RET -eq 0 ]]; then
    git tag -d ${VERSION}
    git tag -a ${VERSION} -m "Version: ${VERSION}"
    git push -q origin build:${BRANCH_NAME} --tags -f
  else
    git tag -a ${VERSION} -m "Version: ${VERSION}"
    git push -q origin build:${BRANCH_NAME} --tags
  fi
  else
    git push -q origin build:${BRANCH_NAME}
  fi
    git checkout master
    git branch -D build
}
if [[ ${LAST_COMMIT_AUTHOR} != "Jenkins" ]]; then
        publish "stable-${GIT_REVISION}"
        replace "stable-${GIT_REVISION}"

        virtualenv --no-site-packages .lime-env
        source .lime-env/bin/activate
        pip install -r test/requirements.txt
        nosetests --verbose --with-xunitmp --nologcapture --xunitmp-file=report.xml test 
        RET=$?
  if [[ $RET -eq 0 ]]; then
    if [[ ${PULL_REQUEST} == "false" ]]; then
      if [[ ! -z $VERSION ]]; then
        update_version
      fi
        publish_github
    fi
  else 
    echo "Tests failed.  See report above" >&2
    exit $RET
  fi
fi

