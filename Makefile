all:
	echo "don't run all tasks" && exit 1

requirements:
	poetry export > requirements.txt
