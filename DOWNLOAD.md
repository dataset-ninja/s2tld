Dataset **S2TLD** can be downloaded in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format):

 [Download](https://assets.supervisely.com/remote/eyJsaW5rIjogImZzOi8vYXNzZXRzLzM0OTdfUzJUTEQvczJ0bGQtRGF0YXNldE5pbmphLnRhciIsICJzaWciOiAiT1U5US9sbEt4dEE3bHJ0RmNCMU0zVnlYTDhVS2txRkI5MzdzeGI3ZGRhdz0ifQ==)

As an alternative, it can be downloaded with *dataset-tools* package:
``` bash
pip install --upgrade dataset-tools
```

... using following python code:
``` python
import dataset_tools as dtools

dtools.download(dataset='S2TLD', dst_dir='~/dataset-ninja/')
```
Make sure not to overlook the [python code example](https://developer.supervisely.com/getting-started/python-sdk-tutorials/iterate-over-a-local-project) available on the Supervisely Developer Portal. It will give you a clear idea of how to effortlessly work with the downloaded dataset.

The data in original format can be downloaded here:

- [S2TLD (1,080 * 1,920)](https://1drv.ms/u/s!Akhz5L4oxpUGiX2BR8RRl4B-XJ4I?e=fFFkll)
- [S2TLD (720 * 1,280)](https://1drv.ms/u/s!Akhz5L4oxpUGigJuXsgf-hyoknPp?e=TjchFL)
