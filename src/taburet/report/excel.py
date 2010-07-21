import pyExcelerator 

def myunicode(string):
    if isinstance(string, str):
        return string.decode('utf8')
    
    return string

def save(book, filename):
    xls_book = pyExcelerator.Workbook()
    
    for sheet in book.sheets:
        xls_sheet = xls_book.add_sheet(myunicode(sheet.name))
        fill_worksheet(sheet, xls_sheet)
        
    xls_book.save(filename)

def fill_worksheet(sheet, xls_sheet):
    for m in sheet._merges:
        xls_sheet.merge(*m)
    
    for c in sheet:
        if c.value == None:
            label = ''
        else:
            label = myunicode(c.value)
        
        xls_sheet.write(c.row, c.column, label, c.style)
        
    for r in sheet._rows.values():
        if r.height:
            style = pyExcelerator.XFStyle()
            style.font.height = r.height
            xls_sheet.row(r.index).set_style(style)
            
    for c in sheet._columns.values():
        if c.width:
            xls_sheet.col(c.index).width = c.width