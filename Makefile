all: 50euro_stat.txt

50euro_stat.txt: mfnf_edit_stat.py
	python3 mfnf_edit_stat.py
