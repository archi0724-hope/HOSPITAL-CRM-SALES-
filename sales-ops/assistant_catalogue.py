"""Private, validated product catalogue setup and useful missing-source responses."""
import csv
import io
import os
import re
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode

FIELDS=['product_name','vendor_name','price','stock','category','manufacturer','specs','warranty']
MAX_BYTES=5*1024*1024


def google_search(message):
    return {'label':'Search Google','url':'https://www.google.com/search?'+urlencode({'q':message})}


def fallback(message):
    if re.fullmatch(r'\s*(?:hi|hello|hey|namaste|namaskar|help)[!.?\s]*',message,re.I):
        reply='Namaste! I am AI Assistance. Ask about saved HOSPkart records or the provided Excel report. For public information, select Google Search. For verified product prices and draft quotations, upload your product catalogue.'
    elif re.search(r'\b(?:quote|quotation|invoice)\b',message,re.I):
        reply='To prepare a product quotation, upload a verified catalogue using Upload catalogue below. I will ask you to confirm quantity, discount and GST before producing a draft. I cannot invent current prices, stock or product specifications. Existing quotation totals remain available under Provided Excel report.'
    else:
        reply='Your CRM and Excel report are available, but no verified product catalogue is loaded yet. Use Upload catalogue for vendor and price searches, or Search Google below for public information. Web results are not verified HOSPkart prices or stock.'
    return {'ok':True,'reply':reply,'assistant':'AI Assistance','provider':'AI Assistance',
            'exports':[],'session_id':None,'catalogue_available':False,'search_actions':[google_search(message)]}


def import_catalogue(upload,target):
    content=upload.read(MAX_BYTES+1)
    if not content or len(content)>MAX_BYTES:raise ValueError('Choose a non-empty catalogue of 5 MB or less.')
    suffix=Path(upload.filename or '').suffix.lower()
    if suffix=='.csv':
        try:rows=csv.reader(io.StringIO(content.decode('utf-8-sig')))
        except UnicodeDecodeError:raise ValueError('Save the CSV with UTF-8 encoding.') from None
    elif suffix=='.xlsx':
        from openpyxl import load_workbook
        try:
            from zipfile import ZipFile
            with ZipFile(io.BytesIO(content)) as archive:
                if sum(item.file_size for item in archive.infolist())>50*1024*1024:
                    raise ValueError('The expanded workbook is too large.')
            workbook=load_workbook(io.BytesIO(content),read_only=True,data_only=True)
            rows=workbook.active.iter_rows(values_only=True)
        except Exception:raise ValueError('This Excel file could not be read. Choose a valid .xlsx catalogue.') from None
    else:raise ValueError('Choose a CSV or XLSX product catalogue.')
    try:
        headers=[str(v or '').strip().lower().replace(' ','_') for v in next(rows)]
        if len(headers)!=len(set(headers)):raise ValueError('Catalogue column names must be unique.')
        missing=set(FIELDS)-set(headers)
        if missing:raise ValueError('Missing catalogue columns: '+', '.join(sorted(missing))+'. Download the template first.')
        parsed=[]
        for number,values in enumerate(rows,2):
            if not any(value is not None and str(value).strip() for value in values):continue
            if len(parsed)>=10000:raise ValueError('Import up to 10,000 products at a time.')
            row={key:str(value if value is not None else '').strip() for key,value in zip(headers,values)}
            if not row.get('product_name') or not row.get('vendor_name'):raise ValueError(f'Row {number}: product and vendor names are required.')
            if any(len(value)>3000 for value in row.values()):raise ValueError(f'Row {number}: a field is too long (maximum 3,000 characters).')
            try:
                price=Decimal(row.get('price',''));stock=Decimal(row.get('stock',''))
                if not price.is_finite() or price<=0 or not stock.is_finite() or stock<0 or stock!=stock.to_integral_value():raise ValueError()
            except (InvalidOperation,ValueError):raise ValueError(f'Row {number}: price must be positive and stock must be a non-negative whole number.') from None
            parsed.append({'id':str(len(parsed)+1),**{key:row.get(key,'') for key in FIELDS},'price':str(price),'stock':str(int(stock))})
        if not parsed:raise ValueError('The catalogue has no product rows.')
    except StopIteration:raise ValueError('The catalogue needs a header row and product rows.') from None
    finally:
        if suffix=='.xlsx' and 'workbook' in locals():workbook.close()
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',dir=target.parent,suffix='.pending',delete=False) as stream:
            temporary=Path(stream.name);writer=csv.DictWriter(stream,fieldnames=['id',*FIELDS]);writer.writeheader();writer.writerows(parsed)
        os.replace(temporary,target)
    finally:
        if temporary and temporary.exists():temporary.unlink()
    return len(parsed)
