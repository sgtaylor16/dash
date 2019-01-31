import pandas as pd
from datetime import datetime as dt
import re

from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource, FactorRange, Label
from bokeh.models.tools import HoverTool
from bokeh.transform import factor_cmap


def dataprep(CRpath,COpath):
    '''
    Function to prepare the raw excel files
    '''

    CRs = pd.read_excel(CRpath,header = 0)
    COs = pd.read_excel(COpath,header = 0)
    #make a temporary column for COs
    tempdf = COs['Actual CO Complete'].copy().to_frame()
    tempdf['today'] = dt.today()
    tempdf = tempdf.min(axis = 1)
    #make a temporary column for CRs
    CRs.loc[CRs['Workflow State'] == 'Complete','Days Open'] = CRs.loc[CRs['Workflow State'] == 'Complete',:].apply(lambda row:row['State Arrival Date'] - row['Start Date'],
        axis = 1)
    CRs.loc[CRs['Workflow State'] != 'Complete','Days Open'] = CRs['Start Date'].apply(lambda x: dt.today() - x)
    CRs['Days Open'] = CRs['Days Open'].apply(lambda x:x.days)


    COs['Days Open'] = tempdf - COs['Actual Start']
    COs['Days Open'] = COs['Days Open'].apply(lambda x:(x.days))

    return [CRs,COs]

def CRprep(CRpath):
    CRs = pd.read_excel(CRpath,header = 0)
    #Calculate days open for CRs
    CRs.loc[CRs['Workflow State'] == 'Complete','Days Open'] = CRs.loc[CRs['Workflow State'] == 'Complete',:].apply(lambda row:row['State Arrival Date'] - row['Start Date'],
           axis = 1)
    CRs.loc[CRs['Workflow State'] != 'Complete','Days Open'] = CRs['Start Date'].apply(lambda x: dt.today() - x)
    CRs['Days Open'] = CRs['Days Open'].apply(lambda x:x.days)
    
    return CRs

def COprep(COpath,CRpath = None):
    COs = pd.read_excel(COpath,header = 0)
    if type(CRpath) == str:
        CRs = CRprep(CRpath)
        
    #make a temporary column for CO's
    tempdf = COs['Actual CO Complete'].copy().to_frame()
    tempdf['today'] = dt.today()
    tempdf = tempdf.min(axis = 1)
    
    #Calculate days open for COs
    COs['Days Open'] = tempdf - COs['Actual Start']
    COs['Days Open'] = COs['Days Open'].apply(lambda x:(x.days))
    
    if type(CRpath) == str:
        CRs = CRprep(CRpath)
        return [COs,CRs]
    else:
        return COs
        
   

def COgannt(COpath,CRpath = None):
    '''
    Function to create a dataframe to plot a Gannt chart for COs
    Keyword Args:
    CRpath - string, path to CR excel file
    COpath - string, path to CO excel file
    '''
#    [CRs,COs] = dataprep(CRpath,COpath)
    [COs,CRs] = COprep(COpath,CRpath)

    #Create a cat type for markets
    markets = ['Child','School Bus','Coach','WTOR','Truck','Defense','Fire','Ambulance','Other','Construction','UTV','Outdoor','Farm','Multiple']
    marketcat = pd.Categorical(markets,markets,ordered = True)
    colors = {'Child':'dodgerblue','School Bus':'orangered','Coach':'coral','WTOR':'orange','Truck':'limegreen','Defense':'olivedrab',
         'Fire':'red','Ambulance':'lightcoral','Other':'lightsalmon','Construction':'gold','UTV':'goldenrod','Outdoor':'brown',
         'Outdoor':'turquoise','Multiple':'black','Farm':'brown'}
    
    #Create a boolean column to filter out random CO's that aren't in any of the desired markets
    testtable = COs['Market'].apply(lambda x: x in markets)
    #Filter out only active CO's in the desired markets
    COs2 = COs.loc[testtable & (COs['Current State'] != 'Active'),:]
    #Get rid of parking lot
    parking = COs2['Current State'].apply(lambda x:'parking' not in x.lower())
    COs2 = COs2.loc[parking,:]
    #Change the market conlumn to a categorical type
    COs2['Market'] = COs2['Market'].astype(marketcat)
    #Sort the markets in the preferred order
    COs2 = COs2.sort_values(by = ['Market','Actual Start'],ascending = False)

    #Create a boolean column to filter out random CR's that aren't in any of the desired markets
    testtable = CRs['Market'].apply(lambda x: x in markets)
    CRstemp = CRs.loc[testtable,:].copy()
    #Find only complete CRs
    CRstemp = CRstemp[CRstemp['Workflow State'] == 'Complete']
    #Change the Market column to a categorical type
    CRstemp['Market'] = CRstemp['Market'].astype(marketcat)
    #Take only the relavent columns and rename hte columns
    CRstemp = CRstemp[['Start Date','State Arrival Date','Number']]
    CRstemp.columns = ['CRStartDate','CRFinishDate','Number']

    #Add New Columns for Plotting and Merging

    #Create regex expression to filter only on the base number
    basenum = re.compile('[0-9]{5}')
    COs2['Base #'] = COs2['CO Number'].apply(lambda x: basenum.search(x)[0])
    CRstemp['Base #'] = CRstemp['Number'].apply(lambda x: basenum.search(x)[0])

    #Add a Colors Column
    COs2['Color']  = COs2['Market'].apply(lambda x:colors[x])

    #Create a Column of today's date
    COs2['Today'] = dt.today()

    #Calculate the Number of days a CR is open and remove those over 14
    CRstemp['CRDaysOpen'] = CRstemp['CRFinishDate'] - CRstemp['CRStartDate']
    CRstemp['CRDaysOpen'] = CRstemp['CRDaysOpen'].apply(lambda x:x.days)
    CRstemp = CRstemp.loc[CRstemp['CRDaysOpen'] <=14,:]


    #Duplicates for Hovertools
    COs2['COName'] = COs2['CO Name']
    COs2['Champ'] = COs2['Project Champion']

    #merge the two files
    COs2 = pd.merge(COs2,CRstemp,left_on = 'Base #',right_on = 'Base #',how = 'left')

    COs2['DaysOpen'] = COs2['Actual Start'].apply(lambda x: dt.today() - x).apply(lambda x:x.days)

    return COs2


def CRgannt(CRpath):
    '''
    Function to create a dataframe to plot a Gannt chart for CRs
    Keyword Args:
    CRpath - string, path to CR excel file
    COpath - string, path to CO excel file
    '''
    CRs = CRprep(CRpath)
    
    #Create Market Data Types
    markets = ['Child','School Bus','Coach','WTOR','Truck','Defense','Fire','Ambulance','Other','Construction','UTV','Outdoor','Farm','Multiple']

    marketcat = pd.Categorical(markets,markets,ordered = True)

    colors = {'Child':'dodgerblue','School Bus':'orangered','Coach':'coral','WTOR':'orange','Truck':'limegreen','Defense':'olivedrab',
         'Fire':'red','Ambulance':'lightcoral','Other':'lightsalmon','Construction':'gold','UTV':'goldenrod','Outdoor':'brown',
         'Outdoor':'turquoise','Multiple':'black','Farm':'brown'}

    
    #Create a boolean column to filter out random CO's that aren't in any of the desired markets
    testtable = CRs['Market'].apply(lambda x: x in markets)
    #Filter out only active CO's in the desired markets
    CRs2 = CRs.loc[testtable & (CRs['Workflow State'] != 'Complete'),:].copy()
    #Get rid of parking lot
    parking = CRs2['Workflow State'].apply(lambda x:'parking' not in x.lower())
    CRs2 = CRs2.loc[parking,:]
    #Change the market conlumn to a categorical type
    CRs2['Market'] = CRs2['Market'].astype(marketcat)
    #Sort the markets in the preferred order
    CRs2 = CRs2.sort_values(by = ['Market','Start Date'],ascending = False)

    #Create a boolean column to filter out random CR's that aren't in any of the desired markets
    testtable = CRs2['Market'].apply(lambda x: x in markets)
    CRs2 = CRs2.loc[testtable,:]

    #Add New Columns for Plotting and Merging

    #Create regex expression to filter only on the base number
    basenum = re.compile('[0-9]{5}')
    CRs2['Base #'] = CRs2['Number'].apply(lambda x: basenum.search(x)[0])

    #Add a Colors Column
    CRs2['Color']  = CRs2['Market'].apply(lambda x:colors[x])

    #Create a Column of today's date
    CRs2['Today'] = dt.today()

    #Rename columns for bokeh (doesn't like spaces)
    CRs2 = CRs2.rename({'Project Champion':'ProjectChampion','Total Days':'TotalDays'},axis = 1)
    
    return CRs2


def CRshow(CRpath, render = False):
    '''
    Creates a bokeh figure object that creates a Gannt chart 
    of CRs in process
    Keyword Arguments:
    CRpath - string, path of excel CR file
    '''

    CRs2 = CRgannt(CRpath)

    CRganntfig = figure(y_range = CRs2['Number'].tolist(), plot_width=1000, plot_height=1000, x_axis_type="datetime",title = 'Open CR\'s')

    #Create a series of dates for today's dates
    source1 = ColumnDataSource(CRs2)

    #CRs
    CRganntfig.hbar(y = 'Number', height = 0.5, left = 'Start Date', right= 'Today',color = 'Color',legend = 'Market',source = source1)

    #Add the Hover Tool
    TOOLTIPS = [
        ('CR Name', "@Name"),
        ("Champ","@ProjectChampion"),
        ("Days Open","@TotalDays"),
        ('Market','@Market')]    

    h = HoverTool(tooltips = TOOLTIPS)   
    CRganntfig.add_tools(h)

    CRganntfig.legend.location = "top_left"
    CRganntfig.legend.label_text_font_size = "6pt"
    CRganntfig.legend.background_fill_alpha = 0.1
    CRganntfig.title.text_font_size = '18pt'
    CRganntfig.title.align = 'center'

    CRganntfig.toolbar.logo = None
    CRganntfig.toolbar_location = None
    
    if render == True:
        show(CRganntfig)

    return CRganntfig


def COshow(CRpath,COpath,render = False):
    '''
    Creates a bokeh figure object that creates a Gannt chart of 
    CO's in process
    Keyworkd Arguments:
    COpath - string, path of excel CRfile
    CRpath - string, path of excel CO file
    '''
    COs2  = COgannt(CRpath,COpath)

    COganntfig = figure(y_range = COs2['CO Number'].tolist(), plot_width=600, plot_height=1000, x_axis_type="datetime",title = 'Open CO\'s')
    
    #Create a series of dates for today's dates
    source1 = ColumnDataSource(COs2)
    
    CRcomp = COs2.dropna(subset = ['Number'])
    source2 = ColumnDataSource(CRcomp)
    
    
    #CO's
    COganntfig.hbar(y = 'CO Number', height = 0.5, left = 'Actual Start',right = 'Today',color = 'Color',legend = 'Market',source = source1)
    #Now the CR's
    COganntfig.hbar(y = 'CO Number',height = 0.5, left = 'CRStartDate',right= 'CRFinishDate',color = None,line_color = 'Color',source = source2)
    
    #Add the Hover Tool
    TOOLTIPS = [
        ('CO Name', "@COName"),
        ("Champ","@Champ"),
        ("Days Open","@DaysOpen"),
        ('Market','@Market')
    ]    
    h = HoverTool(tooltips = TOOLTIPS)   
    COganntfig.add_tools(h)
    
    COganntfig.legend.location = "top_left"
    COganntfig.legend.label_text_font_size = "6pt"
    COganntfig.legend.background_fill_alpha = 0.1
    COganntfig.title.text_font_size = '18pt'
    COganntfig.title.align = 'center'
    
    COganntfig.toolbar.logo = None
    COganntfig.toolbar_location = None
    
    if render == True:
        show(COganntfig)
        
    return COganntfig
    
#Now Work on the Weekly Statistics

def CRweekly(CRpath,render = False):
    CRs = CRprep(CRPath)
    
    #Create a df of only complete CRs
    completeCRs = CRs.loc[CRs['Workflow State'] == 'Complete',:].copy()
    
    #Create a calculated column of days to complete
    completeCRs.loc[:,'Days'] = completeCRs['State Arrival Date'] - completeCRs['Start Date']
    completeCRs['Days'] = completeCRs['Days'].apply(lambda x:x.days)
    #Calculate mean number of days to complete a CR, sampled weekly
    meanCRs = pd.Series(data = completeCRs['Days'].tolist(),index = completeCRs['State Arrival Date']).resample('W').mean()
    meanCRs = meanCRs.to_frame()
    
    #Create Series of CRs open and closed dates
    CRsopen = pd.Series(data = CRs['Number'].tolist(),index = CRs['Start Date'])
    CRsclosed = pd.Series(data  = completeCRs['Number'].tolist(),index = completeCRs['State Arrival Date'])
    
    #Count CRs open and closed by week
    CRopencount = CRsopen.resample('W').count().to_frame()
    CRclosedcount = CRsclosed.resample('W').count().to_frame()
    
    
    CRcounts = pd.merge(CRopencount,CRclosedcount,left_index = True,right_index = True,how = 'outer').fillna(0)
    CRcounts = pd.merge(CRcounts,meanCRs,left_index = True,right_index = True,how = 'outer').fillna(0)
    CRcounts.columns = ['Open','Closed','Mean']
    CRcounts = CRcounts.iloc[-12:,:]
    CRcounts = CRcounts.reset_index()
    CRcounts = CRcounts.rename({'index':'Week'},axis = 1)
    CRcounts['Week'] = CRcounts['Week'].astype(str)
    
    x = [(week1,status) for week1 in CRcounts['Week'] for status in ['Open','Closed']]
    counts = sum(zip(CRcounts['Open'], CRcounts['Closed']), ()) # like an hstack
    source = ColumnDataSource(data=dict(x=x, counts=counts))
    
    CRmetrics = figure(x_range=FactorRange(*x), plot_width = 600,plot_height = 400,title="CR History",
               toolbar_location=None, tools="")
    CRmetrics.vbar(x='x', top='counts', width=0.8, source=source)
    CRmetrics.line(x = CRcounts['Week'].tolist(),y = CRcounts['Mean'].tolist(),line_width = 3,color = 'red')
    CRmetrics.xaxis.major_label_orientation = 1
    
    CRmetrics.toolbar.logo = None
    CRmetrics.toolbar_location = None
    
    if render == True:
        show(CRmetrics)
        return None
    else:
        return CRmetrics
    
def COweekly(COPath,render = False):
    
    COs = COprep(COPath)
    
    #Find the complete COs
    completeCOs = COs.loc[COs['Actual CO Complete'].apply(lambda x: not pd.isnull(x)),:].copy()
    
    #Create a a column of days to complete a given CO
    completeCOs['Days to Complete'] = completeCOs['Actual CO Complete'] - completeCOs['Actual Start']
    completeCOs['Days to Complete'] = completeCOs['Days to Complete'].apply(lambda x: x.days)
    
    #Calculate the mean days to complete a CO sampled weekly
    meanCOs = pd.Series(data = completeCOs['Days to Complete'].tolist(),index = completeCOs['Actual CO Complete'].tolist()).resample('W').mean()
    meanCOs = meanCOs.to_frame()
    
    
    #Calculate columns of when given COs where open and closed
    tempCOs = COs.dropna(subset = ['Actual Start'])
    COsopen = pd.Series(data = tempCOs['CO Number'].tolist(),index = tempCOs['Actual Start']).sort_index()
    COsclosed = pd.Series(data  = completeCOs['CO Number'].tolist(),index = completeCOs['Actual CO Complete'])
    
    #Count the open and closed CO's sampled weekly
    COopencount = COsopen.resample('W').count().to_frame()
    COclosedcount = COsclosed.resample('W').count().to_frame()
    
    #Merge the columns
    COcounts = pd.merge(COopencount,COclosedcount,left_index = True,right_index = True,how = 'outer').fillna(0)
    COcounts = pd.merge(COcounts,meanCOs,left_index = True,right_index = True,how = 'outer').fillna(0)
    COcounts.columns = ['Open','Closed','Mean']
    #Fileter out only the last 15 weeks for plotting
    COcounts = COcounts.iloc[-15:,:]
    COcounts = COcounts.reset_index()
    COcounts = COcounts.rename({'index':'Week'},axis = 1)
    #Convert the weeks from datetime to string so I can treat it as categorical in bokeh plots
    COcounts['Week'] = COcounts['Week'].astype(str)
    COcounts['Week'] = COcounts['Week'].apply(lambda x:x[5:])
    
    #Create the bokeh plot
    palette = ['lime','aqua']
    x = [(week1,status) for week1 in COcounts['Week'] for status in ['Open','Closed']]
    counts = sum(zip(COcounts['Open'], COcounts['Closed']), ()) # like an hstack
    source = ColumnDataSource(data=dict(x=x, counts=counts))
    
    COmetrics = figure(x_range=FactorRange(*x), plot_width = 600,plot_height = 400,title="CO History",
               toolbar_location=None, tools="")
    COmetrics.vbar(x='x', top='counts', width=0.8, source=source,
                  fill_color=factor_cmap('x', palette=palette, factors=['Open','Closed'],start=1, end=2))
    COmetrics.line(x = COcounts['Week'].tolist(),y = COcounts['Mean'].tolist(),line_width = 3,color = 'red')
    COmetrics.xaxis.major_label_orientation = 1
    
    COmetrics.toolbar.logo = None
    COmetrics.toolbar_location = None
    
    if render == True:
        show(COmetrics)
        return None
    else:
        return COmetrics
        
 
    


