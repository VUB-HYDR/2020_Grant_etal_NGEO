#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 13:18:37 2019

@author: Luke
"""


#==============================================================================
# SUMMARY
#==============================================================================


# 09 March 2020

# This script is used to plot historical-future scaled signals in ice thickness for
# 3 seasons across all available lake models

# converted whole plotting scheme to function for main_p1.py
# have commented out (because main script handles these):
#   directory calls
#   flag for svplt
#   flag for mmm or subplot


#==============================================================================
# IMPORT
#==============================================================================


import xarray as xr
import os
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib as mpl


#==============================================================================
# FUNCTIONS
#==============================================================================


# reading netcdfs
def reader(filename):
    ds = xr.open_dataset(filename, decode_times=False)
    da = ds.icethick
    dims = list(da.dims)
    discard = []
    if 'time' in dims:
        discard.append('time')
    if 'levlak' in dims:
        discard.append('levlak')
    da.squeeze(dim=discard,drop=True)
    return da

# reading netcdfs (adjusted for LAKE)
def LAKEreader(filename,clm_lon,clm_lat):
    ds = xr.open_dataset(filename, decode_times=False)
    ds['lon'] = clm_lon
    ds['lat'] = clm_lat
    da = ds.icethick
    dims = list(da.dims)
    discard = []
    if 'time' in dims:
        discard.append('time')
    if 'levlak' in dims:
        discard.append('levlak')
    da.squeeze(dim=discard,drop=True)
    return da

# ensemble math
def ensembler(arrays):
    concat_dim = np.arange(len(arrays))
    aligned = xr.concat(arrays,dim=concat_dim)
    mean = aligned.mean(dim='concat_dim')
    return mean

# processing function
def itscalesig_proc(inDIR):
    
    # set directory
    os.chdir(inDIR)
    
    #==============================================================================
    #DEFINE LOAD SETTINGS
    #==============================================================================
                    
    flag_var=2;  # 0: watertemp
                 # 1: lakeicefrac
                 # 2: icethick
                 # 3: icestart
                 # 4: iceend
                 # 5: icedur
     
    flag_prod=2; # 0: fldmean
                 # 1: sig
                 # 2: scaled_sig
                 # 3: eval
    
    # list of models (filename format)
    models = ['clm45','albm','simstrat-uog','vic-lake','lakemod'] # temporarily removed "lake"
    
    # list of variables (1st root variables, then processed)
    variables = ['watertemp','lakeicefrac','icethick','icestart','iceend','icedur']
    
    # list of products
    products = ['fldmean','sig','scaled_sig','eval']
    
    # list of rcps (no flagging)
    rcps = ['rcp26','rcp60','rcp85']
    
    # list of seasons (no flagging; for file querying and figure panel IDs)
    seasons = ['SON','DJF','MAM']
    
    # assert settings
    var = variables[flag_var]
    prod = products[flag_prod]
    
    #==============================================================================
    #ACCESS FILES
    #==============================================================================
    
    files = []
    for rcp in rcps:
        for seas in seasons:
            for file in [file for file in sorted(os.listdir(inDIR))\
                     if var in file and rcp in file and seas in file and prod in file]:
                files.append(file)
                
    # filter model names iterable for existing model data for evaluation
    available_models = []
    for mod in models:
        count = 0
        for file in files:
            if mod in file:
                count = count+1
                if count == 1:
                    available_models.append(mod)
    
    #==============================================================================
    #OPEN MODEL TIMMEANS
    #==============================================================================
    
    # arrange + read files  
    arrays = {}
    for rcp in rcps:
        arrays[rcp] = {}
        for mod in available_models:
            arrays[rcp][mod] = {}
            for seas in seasons:
                for file in files:
                    count = 0
                    if mod != 'lakemod':
                        if rcp in file and mod in file and seas in file:
                            arrays[rcp][mod][seas] = reader(file)
                            count += 1
                            if count == 1:
                                if mod == 'clm45': # grabbing new coord dims for LAKE data-arrays
                                    clm_lat = arrays[rcp][mod][seas].lat
                                    clm_lon = arrays[rcp][mod][seas].lon
                    elif mod == 'lakemod':
                        if rcp in file and mod in file and seas in file:
                            arrays[rcp][mod][seas] = LAKEreader(file,clm_lon,clm_lat)
    
    # add key for multi-model mean
    for rcp in rcps:    
        arrays[rcp]['mmm'] = {}
        for seas in seasons:
            temp_list = []
            for mod in available_models:
                temp_list.append(arrays[rcp][mod][seas])
            arrays[rcp]['mmm'][seas] = ensembler(temp_list)
    
    # arange for plotting
    multimodel = {}
    for rcp in rcps:    
        multimodel[rcp] = [arrays[rcp]['mmm']['SON'],arrays[rcp]['mmm']['DJF'],arrays[rcp]['mmm']['MAM'],\
                           arrays[rcp]['clm45']['SON'],arrays[rcp]['clm45']['DJF'],arrays[rcp]['clm45']['MAM'],\
                           arrays[rcp]['simstrat-uog']['SON'],arrays[rcp]['simstrat-uog']['DJF'],arrays[rcp]['simstrat-uog']['MAM'],\
                           arrays[rcp]['albm']['SON'],arrays[rcp]['albm']['DJF'],arrays[rcp]['albm']['MAM'],\
                           arrays[rcp]['lakemod']['SON'],arrays[rcp]['lakemod']['DJF'],arrays[rcp]['lakemod']['MAM']]
        
    lat = arrays['rcp26']['clm45']['SON'].lat.values
    lon = arrays['rcp26']['clm45']['SON'].lon.values
    
    return multimodel,lat,lon
    
# plotting function
def itscalesig_plot(multimodel,lat,lon,outDIR,flag_svplt,var,prod,dpi):
    
    # list of rcps (no flagging)
    rcps = ['rcp26','rcp60','rcp85']
    
    # list of seasons (no flagging; for file querying and figure panel IDs)
    seasons = ['SON','DJF','MAM']
    
    #==============================================================================
    #DEFINE PLOT SETTINGS
    #==============================================================================
    
    # font settings
    title_font = 13
    cbtitle_font = 13
    tick_font = 11
    arrow_font = 13
    
    # continent fill
    col_cont='white'
    
    # ocean fill
    col_ocean='lightgrey'
    
    # zero change color
    col_zero='gray'
    
    # list of model titles
    model_titles = ['Multi-model mean', 'CLM4.5', 'SIMSTRAT-UoG', 'ALBM', 'LAKE']
    
    # list of figure panel ids
    letters = ['a', 'b', 'c',\
               'd', 'e', 'f',\
               'g', 'h', 'i',\
               'j', 'k', 'l',\
               'm', 'n', 'o']
    
    #========== COLORBAR ==========#
    
    # identify colors
    cmap_whole = plt.cm.get_cmap('PRGn_r')
    cmap55 = cmap_whole(0.01)
    cmap50 = cmap_whole(0.05)   #green
    cmap45 = cmap_whole(0.1)
    cmap40 = cmap_whole(0.15)
    cmap35 = cmap_whole(0.2)
    cmap30 = cmap_whole(0.25)
    cmap25 = cmap_whole(0.3)
    cmap20 = cmap_whole(0.35)
    cmap15 = cmap_whole(0.4)
    cmap10 = cmap_whole(0.45)
    cmap0 = col_zero
    cmap_5 = cmap_whole(0.55)
    cmap_10 = cmap_whole(0.6)
    cmap_20 = cmap_whole(0.65)
    cmap_25 = cmap_whole(0.7)
    cmap_30 = cmap_whole(0.75)
    cmap_35 = cmap_whole(0.8)
    cmap_40 = cmap_whole(0.825)
    cmap_45 = cmap_whole(0.875)
    cmap_50 = cmap_whole(0.925)  #purple
    cmap_55 = cmap_whole(0.99)
    
    # declare list of colors for discrete colormap of colorbar
    cmap = mpl.colors.ListedColormap([cmap_55,cmap_50,cmap_45,cmap_40,\
                                      cmap_35,cmap_30,cmap_25,cmap_20,cmap_10,cmap_5],N=10)
    
    # set color of over/under arrows in colorbar
    cmap.set_over(cmap30)
    cmap.set_under(cmap_55)
    
    # colorbar args
    values = [-1.0,-0.9,-0.8,-0.7,-0.6,-0.5,-0.4,-0.30,-0.20,-0.10,0]
    tick_locs = [-1.0,-0.9,-0.8,-0.7,-0.6,-0.5,-0.4,-0.30,-0.20,-0.10,0]
    norm = mpl.colors.BoundaryNorm(values,cmap.N)
    
    # bbox (arrow plot relative to this axis)
    cb_x0 = 0.225
    cb_y0 = 0.22
    cb_xlen = 0.55
    cb_ylen = 0.01
    
    # colorbar label
    cblabel = 'Change in seasonal ice thickness scaled by global mean air temperature (m/°C)'
    
    #========== ARROWS ==========#
    
    # green arrow label
    greenlabel = 'Lower sensitivity'
    x0_greenlab = 0.75
    y0_greenlab = -2.7
    
    # green arrow
    x0_greenarr = 0.505
    y0_greenarr = -3.3
    xlen_greenarr = 0.4
    ylen_greenarr = 0
    
    # purple arrow label
    purplelabel = 'Higher sensitivity'
    x0_purplelab = 0.25
    y0_purplelab = -2.7
    
    # purple arrow
    x0_purplearr = 0.495
    y0_purplearr = -3.3
    xlen_purplearr = -0.4
    ylen_purplearr = 0
    
    # general
    arrow_width = 0.25
    arrow_linew = 0.1
    arrow_headwidth = 0.5
    arrow_headlength = 0.06
    
    #========== SUBPLOTS ==========#
    
    left_border = 0.15
    right_border = 0.85
    bottom_border = 0.25
    top_border = 0.925
    width_space = 0.05
    height_space = 0.05
    
    # figsize = (x,y)
    x = 15
    y = 25
    
    #==============================================================================
    #INITIALIZE PLOTTING
    #==============================================================================
    
    lon, lat = np.meshgrid(lon, lat)
    
    for rcp in rcps:
        
        data = multimodel[rcp]
        
        f, axes = plt.subplots(int(len(data)/3),3,figsize=(x,y));
        
        count = 0
        
        for ax,array in zip(axes.flatten(),data):
            
            count = count+1
            
            m = Basemap(projection='npaeqd',round=True,boundinglat=20,\
                        lat_0=80,lon_0=0,resolution='l');
            m.ax = ax
            m.drawcoastlines(linewidth=0.05);
            m.drawmapboundary(linewidth=0.15,fill_color=col_ocean);
            m.fillcontinents(color=col_cont);
            m.pcolormesh(lon,lat,array,latlon=True,cmap=cmap,norm=norm,vmax=0,vmin=-1.0,zorder=3)
            ax.set_title(letters[count-1],loc='left',fontsize=title_font,fontweight='bold')
            if count<=3:
                ax.set_title(seasons[count-1],loc='center',pad=10,fontsize=title_font)
            if count == 1:
                ax.set_ylabel(model_titles[0],fontsize=title_font,labelpad=15)
            if count == 4:
                ax.set_ylabel(model_titles[1],fontsize=title_font,labelpad=15)
            if count == 7:
                ax.set_ylabel(model_titles[2],fontsize=title_font,labelpad=15)
            if count == 10:
                ax.set_ylabel(model_titles[3],fontsize=title_font,labelpad=15)
            if count == 13:
                ax.set_ylabel(model_titles[4],fontsize=title_font,labelpad=15)
                
                
        #colorbar setup
        cbax = f.add_axes([cb_x0, cb_y0, cb_xlen, cb_ylen])
        cb = mpl.colorbar.ColorbarBase(ax=cbax,cmap=cmap,
                                       norm=norm,
                                       spacing='uniform',
                                       orientation='horizontal',
                                       extend='both',
                                       ticks=tick_locs)
        cb.set_label(cblabel,size=cbtitle_font)
        cb.ax.xaxis.set_label_position('top');
        cb.ax.tick_params(labelcolor='0.2',labelsize=tick_font,color='0.2',\
                          length=2.5,width=0.35,direction='out'); 
        cb.ax.set_xticklabels([r'$\leq$-1.0','-0.9','-0.8','-0.7','-0.6',\
                               '-0.5','-0.4','-0.3','-0.2','-0.1','0'])
        cb.outline.set_edgecolor('0.2')
        cb.outline.set_linewidth(0.4)
        
        # arrow setup
        plt.text(x0_greenlab, y0_greenlab, greenlabel, size=arrow_font, ha='center', va='center')
        plt.text(x0_purplelab, y0_purplelab, purplelabel, size=arrow_font, ha='center', va='center')
        plt.arrow(x0_greenarr, y0_greenarr, xlen_greenarr, ylen_greenarr, width=arrow_width, linewidth=arrow_linew,\
                  shape='right', head_width=arrow_headwidth, head_length=arrow_headlength,\
                  facecolor=cmap40, edgecolor='k', clip_on=False)
        plt.arrow(x0_purplearr, y0_purplearr, xlen_purplearr, ylen_purplearr, width=arrow_width, linewidth=arrow_linew,\
                  shape='left', head_width=arrow_headwidth, head_length=arrow_headlength,\
                  facecolor=cmap_40, edgecolor='k', clip_on=False)
        
        plt.subplots_adjust(left=left_border, right=right_border, bottom=bottom_border, top=top_border,\
                            wspace=width_space, hspace=height_space)
        plt.show()
    
        # save figure
        if flag_svplt == 0:
            None
        elif flag_svplt == 1:
            if rcp == 'rcp26':
                f.savefig(outDIR+'/si_f11.png',bbox_inches='tight',dpi=dpi)
            elif rcp == 'rcp60':
                f.savefig(outDIR+'/si_f12.png',bbox_inches='tight',dpi=dpi)
            elif rcp == 'rcp85':
                f.savefig(outDIR+'/si_f13.png',bbox_inches='tight',dpi=dpi)
    
