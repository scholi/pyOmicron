all: GUI_STSviewer.py

GUI_STSviewer.py: GUI_STSviewer.ui
	pyuic4 $< > $@
	rm -f $*.pyc
