#!/bin/bash

./cancelall.sh
sbatch softIoc.batch
sbatch logger.batch
sbatch opc.batch
sbatch aeth.batch
sbatch sniffer.batch
sbatch mariadb.batch
