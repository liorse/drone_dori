#!/bin/bash
scancel -w node01
sudo scontrol update nodename=node01 state=idle
rm slurm*
