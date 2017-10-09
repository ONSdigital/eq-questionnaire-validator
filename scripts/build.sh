#!/usr/bin/env bash

printf $(git rev-parse HEAD) > .application-version
