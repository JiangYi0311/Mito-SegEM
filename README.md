# Mito-SegEM
## Introduction
Recent technical advances in volume electron microscopy (vEM) and artificial intelligence-assisted image processing have facilitated high throughput quantifications of cellular structures, such as mitochondria that are ubiquitous and morphologically diversified. A still often overlooked computational challenge is to assign cell identity to numerous mitochondrial instances, for which both mitochondrial and cell membrane contouring used to be required. Here, we present a vEM reconstruction procedure (called mito-segEM) that utilizes virtual path-based annotation to assign automatically segmented mitochondrial instances at the cellular scale, therefore bypassing the requirement of membrane contouring. The embedded toolset in webKnossos (an open-source online annotation platform) is optimized for fast annotation, visualization, and proofreading of cellular organelle networks. We demonstrate broad applications of mito-segEM on volumetric datasets from various tissues, including the brain, intestine, and testis, to achieve an accurate and efficient reconstruction of mitochondria in a use-dependent fashion. 

## Installation
### PyTorch Connectomics
The deep learning framework powered by PyTorch for automatic and semi-automatic semantic and instance segmentation in connectomics was provided by the Visual Computing Group (VCG) at Harvard University.  
Refer to the [Pytorch Connectomics wiki](https://connectomics.readthedocs.io/en/latest/), specifically the [installation page](https://connectomics.readthedocs.io/en/latest/notes/installation.html), for the most up-to-date instructions on installation on a local machine or high-performance cluster.
### Install webKnossos
WEBKNOSSOS is open-source, so you can install it on your own server.
[Check out the documentation](https://docs.webknossos.org/webknossos/installation.html) for a tutorial on how to install WEBKNOSSOS on your own server.
### Some key dependency libraries
pytorch  
webknossos  
fastremap  
h5py  
tifffile  
zarr  
## Pipeline
### Mitochondrial segmentation
The pre-trained mitochondrial segmentation model (Lu et al., 2024) was based on a residual 3D U-Net architecture with four-down/four-up layers, which was provided by PyTorch Connectomics. The model was trained to classify each voxel of the input stack (17 consecutive 256 × 256 pixel-sized images) into the “background”, “mitochondrial mask”, and “mitochondrial contour” categories. The model output was a two-channel image stack with the same format as the input, including the predicted probability maps of mitochondrial masks and contours.
![Architecture of mitochondrial segmentation and reconstruction](https://github.com/JiangYi0311/Mito-assignment/blob/main/figures/Pipeline%20of%20mitochondrial%20segmentation.png)  
To generate mitochondrial instance masks, the seeds of mitochondria (or markers) were determined with a high mask probability and low contour probability by thresholding. Then, the marker-controlled watershed transform algorithm (part of the scikit-image library) was employed to generate high-quality instance masks of mitochondria with the seed locations and the predicted probability map of the masks.  
### Segmentation import into webKnossos
The segmentation of mitochondria was imported into the webKnossos using Python scripts.  
**run segmentation_to_webknossos.py**
### Mitochondria assignment by a virtual path
In the “toggle merger mode” and with the option “hide the unmapped segmentation” selected, a start point was seeded and associated mitochondria were annotated one after another through the mouse right-clicks within individual instances. Upon each valid assignment, the corresponding mitochondrial instance would become visible with a pseudo-color and linked by an active node, so that missing and multiple annotations of mitochondrial instances could be minimized. Note that the “toggle merger mode” does not allow a mouse click outside the segments and ignores redundant annotations of a single segment. Finally, the assembly of the nodes was utilized to specify the associated mitochondrial instances that could be then operated as a defined group with i.e. self-written Python scripts.  
### Proofreading and downloading

### Quantitative analysis and 3D rendering
#### Quantitative analysis
The nodes of mitochondria are based on virtual path annotation, which could be extracted from webKnossos.  
**run extract_virtual_path_node_info.py**  
  
All mitochondrial volume was precomputed.  
**run volume_precomputation.py**  
  
The mitochondrial complexity index(MCI) was computed.  
**run compute_MCI.py**  
#### 3D rendering
Here, we used Amria software to 3D render the reconstruction of mitochondria in various cells.  
![Mitochondria of intestinal and testis cells](https://github.com/JiangYi0311/Mito-SegEM/blob/main/figures/Mitochondria%20of%20intestinal%20and%20testis%20cells.png =1000x)
