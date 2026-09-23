"""Visually reviewed caption regions, tied to exact page filenames (never reused).

Coordinates describe printed captions, not photographs or nearest products.
Grid cells only locate the caption; they are never clickable themselves.
"""
STAMP='202609090934-page_'
X=[20,184,350,517,683,850,1016,1181]
Y=[69,237,406,575,744,913,1083,1250]

def reviewed(page,url):
    if STAMP not in url:return None
    out=[]
    def add(box,name=None,price_box=None,price=None,**extra):
        out.append(dict(caption=box,name=name,priceBox=price_box,price=price,**extra))
    def circle(x,y,w=100,h=86,name=None,price=None):
        add([x+12,y+8,w-24,int(h*.49)],name,[x+16,y+int(h*.54),w-25,int(h*.42)],price)
    def cell(r,c,rs=1,cs=1,side=False):
        x,y,x1,y1=X[c],Y[r],X[c+cs],Y[r+rs]
        if side:box=[x1-56,y+8,52,y1-y-48]
        else:box=[x+3,y1-48,x1-x-58,45]
        add(box,price_box=[x1-53,y1-37,50,34])
    def grid(skip=(),merges=(),right=()):
        covered=set(skip);starts={}
        for r,c,rs,cs in merges:
            starts[r,c]=(rs,cs)
            covered.update((rr,cc) for rr in range(r,r+rs) for cc in range(c,c+cs) if (rr,cc)!=(r,c))
        for r in range(7):
            for c in range(7):
                if (r,c) in covered:continue
                rs,cs=starts.get((r,c),(1,1));cell(r,c,rs,cs,(r,c) in right)
    if page==1:
        for b,name,pb,price in [
          ([182,328,75,77],'Coricelli olio extra vergine di oliva 1 l',[180,429,68,43],4.99),
          ([445,330,113,101],'De Cecco pasta di semola Limited Edition 500 g',[468,454,73,41],.69),
          ([650,344,65,62],'Mutti passata di pomodoro 700 g',[646,429,72,40],.89),
          ([79,604,115,53],"As do Mar tonno all’olio di oliva 70 g x 12",[218,610,77,43],8.99),
          ([471,611,86,87],'Arborea latte italiano UHT parzialmente scremato 1 l',[473,719,70,44],.79),
          ([782,599,58,54],'Pavesi Gocciole 1 kg',[775,665,67,45],3.49),
          ([902,637,87,53],'Sao caffè intenso 250 g x 4',[1030,643,62,44],9.99),
          ([117,956,110,51],'Findus 24 + 6 bastoncini 750 g',[251,962,68,46],5.99),
          ([513,904,43,49],'Peroni birra 66 cl',[507,977,61,39],.89),
          ([639,910,77,51],'Scottonelle carta igienica 12 rotoli',[760,913,68,46],3.99),
          ([881,922,80,76],'Omino Bianco detersivo lavatrice 35 lavaggi 1,1 l x 3',[889,1015,70,43],8.99)]:add(b,name,pb,price)
        for i,name in enumerate(['Salsicce rustiche','Arista tranci o fette','Macinato scelto di suino','Fettine di pancetta','Fettine di prosciutto','Bistecche di lombo','Spuntature di suino pacco famiglia']):
            add([1075,303+i*12,112,13],name,price=4.99,format='al kg')
    elif page==2:
        for x,y,name in [(369,150,'Salsiccia macinata rustica'),(725,102,'Fettine di prosciutto di suino'),(1060,102,'Bistecche di lombo di suino'),(38,265,'Macinato scelto di suino'),(344,367,'Spuntature di suino pacco famiglia'),(655,373,'Fettine di pancetta di suino'),(989,367,'Arista di suino intera o fette')]:
            add([x+13,y+17,74,51],name,price=4.99,format='al kg')
        for x,y,name,price in [(164,497,'Fettine sceltissime tutti i tagli di bovino danese',17.99),(48,605,'Fiorentina di costata di bovino danese',16.99),(704,595,'Picanha di bovino danese',19.99),(1052,591,'Bistecca di reale di bovino danese',15.99),(621,759,'Tagliata di bovino danese',15.99),(1052,751,'Macinato di bovino danese',14.99),(156,891,'Fettine sceltissime di fracosta di bovino adulto',14.99),(768,894,'Bollito senza osso di bovino adulto',13.99),(887,887,'Straccetti di bovino adulto',18.99),(31,980,'Fiorentina di costata di bovino adulto',16.99),(384,1151,'Fettine di girello di bovino adulto',16.99),(652,1143,'Hamburger scelti di bovino adulto',9.99),(917,1151,'Macinato scelto di bovino adulto',9.99)]:circle(x,y,name=name,price=price)
    elif page==3:
        for x,y,name,price in [(353,99,'Sovracosce di pollo',3.99),(715,84,'Pollo alla diavola',3.99),(42,234,'Coscio di pollo alla diavola',2.99),(380,352,'Cosciotto di pollo',2.99),(710,243,'Spezzato di pollo',3.99),(855,224,'Macinato e hamburger di bovino adulto',9.99),(845,346,'Tagliata di manzo danese',15.99),(296,505,'Bocconcini magri di vitella',11.99),(29,578,'Macinato di vitella',12.99),(765,497,'Fettine scelte di vitella',15.99),(1053,488,'Bistecca di fracosta con osso di vitella',9.99),(303,737,'Ossobuchi di vitella',10.99),(718,671,'Vitello porchettato',10.99),(868,691,'Braciole di petto di vitella',10.99),(472,969,'Cotolette di maialino',7.99),(42,1080,'Coscio di maialino',6.99),(199,1148,'Maialino porzionato',5.99)]:circle(x,y,name=name,price=price)
        for x,y,name in [(917,934,'AIA I Panati Cordon Bleu 735 g'),(608,985,'AIA I Panati cotolette con spinaci 770 g'),(606,1146,'AIA I Panati nuggets bocconcini di pollo 710 g'),(895,1140,'AIA I Panati cotolette di pollo e tacchino 770 g')]:circle(x,y,82,72,name,3.99)
    elif page==4:
        add([37,337,178,62],"Recla prosciutto cotto Praga l’etto",[264,345,78,56],.79)
        for c in range(2,7):cell(0,c,side=c==5)
        cell(1,2);cell(1,3,cs=2,side=True);cell(1,5);cell(1,6)
        for c in range(7):cell(2,c,side=c==2);cell(3,c)
        cell(4,3,cs=2,side=True);cell(4,5);cell(4,6,side=True)
        for r in [5,6]:
            for c in range(3,7):cell(r,c)
    elif page==5:
        for r in [0,1]:
            for c in range(5):cell(r,c)
        add([1026,339,105,61],"Galbani Certosa l’etto",[872,351,75,50],1.09)
        for x,y,name,price in [(226,454,'Trote salmonate',6.99),(824,456,'Filetto di persico',12.99),(80,735,'Cozze Italia',3.99),(534,844,'Tranci di salmone',12.99),(1028,745,'Tentacoli di totano',5.99),(80,1121,'Calamari decongelati',15.99),(955,1085,'Orate 400/600',7.99)]:circle(x,y,108,95,name,price)
    elif page==6:
        for x,y,name,price in [(198,57,'Uva bianca senza semi 500 g',1.29),(752,42,'Susine scure variegate',1.49),(32,165,'Selenella cipolle dorate 750 g',.99),(214,189,'Selenella cipolle rosse 750 g',.99),(625,164,"Fichi d’India vaschetta 500 g",.99),(354,210,'Limoni in rete 1 kg',1.49),(723,254,'Mele Royal Gala cal. 70-75 sacchetto 3 kg',2.49),(966,212,'Orchidea vaso 12',4.99),(349,380,'Pomodoro oblungo rosso',.99),(141,482,'Consilia fagiolini 500 g',1.69),(640,496,'Zucca Vanity',1.59),(853,444,'Selenella patate al selenio 1,5 kg',2.49),(339,547,'Dole banane',1.49),(650,627,'Mele Giga cal. 80-85',1.69),(979,597,'Ficus Beniamin vaso 16',5.99)]:circle(x,y,110,97,name,price)
        cell(4,0,rs=2);cell(4,1);cell(4,2,cs=2,side=True)
        for c in [4,5,6]:cell(4,c)
        for c in range(1,7):cell(5,c,side=c==3)
        for c in range(7):cell(6,c,side=c in [0,1,5,6])
    elif page==7:
        grid(skip=[(6,0),(6,5),(6,6)],merges=[(0,4,2,1),(3,1,1,2),(4,3,2,1),(6,2,1,2)],right=[(0,5),(1,0),(2,0),(2,2),(3,1),(4,0),(6,2)])
        add([859,1115,72,65],'Consilia drink senza zuccheri aggiunti bio 1 l',[861,1180,70,29],1.49,validTo='2026-09-30')
        add([1075,1103,94,52],'Consilia pasta di semola integrale bio 500 g',[1104,1153,68,32],.79,validTo='2026-09-30')
    elif page==8:grid(right=[(1,3),(2,0),(2,4),(4,5),(4,6),(6,0)])
    elif page==9:grid(merges=[(3,3,1,2)],right=[(0,2),(1,3),(2,1),(3,2),(3,3),(6,6)])
    elif page==10:grid(merges=[(0,0,1,2),(1,3,1,2),(5,5,1,2)],right=[(0,0),(1,1),(1,2),(1,3),(2,3),(2,4),(2,5),*[(3,c) for c in range(1,7)],*[(4,c) for c in range(7)],(5,0),(5,1),(5,5)])
    elif page==11:grid(skip=[(0,4)],merges=[(2,2,2,1)],right=[(0,0),(0,3),(0,5),(2,3),(3,3),(3,6),(4,0),(4,1),(4,2),(4,4),(4,5),(5,3),(5,4),(6,0),(6,4)])
    elif page==12:grid(merges=[(3,1,1,2),(6,3,1,2)],right=[(0,6),(1,1),(1,4),(1,5),(2,1),(2,5),(3,0),(3,1),(3,4),(4,0),(4,2),(4,6),(5,0),(5,1),(5,4),(5,5),(6,1),(6,3)])
    elif page==13:grid(right=[(0,0),(1,1),(1,2),(1,3),(3,2),(3,3),(3,4),(3,5),(4,2),(4,3),(4,4),(4,6),(5,0),(5,1),(5,3),(5,5),(6,6)])
    elif page==14:grid(right=[(r,c) for r in range(7) for c in range(7) if (r,c)!=(5,1)])
    elif page==15:grid(skip=[(5,0)],merges=[(5,1,2,1)],right=[(0,0),(0,5),(1,0),(2,0),(2,5),(2,6),(3,1),(3,2),(3,3),(3,4),(3,6),(4,0),(4,1),(4,2),(4,3),(4,5),(5,6),(6,3),(6,4),(6,6)])
    elif page==16:
        for box,name,pb,price,day in [
          ([235,197,62,73],'Valfrutta passata di pomodoro al vapore 700 g',[245,304,54,35],.79,'13'),
          ([521,198,64,62],"Caffè Trombetta L’Espresso 100 capsule",[527,301,59,39],19.99,'13'),
          ([245,426,51,45],'Ichnusa birra 66 cl',[245,505,54,35],.99,'13'),
          ([233,614,65,58],'Regina Blitz asciugatutto monovelo',[247,702,53,38],1.99,'13'),
          ([330,695,170,44],'Dash Power detersivo liquido 20 lavaggi x 2 900 ml',[536,704,50,36],6.99,'13'),
          ([1108,225,66,46],'Lavazza caffè Suerte 250 g x 4',[1126,301,55,39],9.99,'20'),
          ([831,414,61,57],'Fiorucci prosciutto cotto vellutato 2 etti',[842,500,50,38],1.00,'20'),
          ([1126,426,51,31],'Ferrero Nutella 950 g',[1128,503,53,37],5.99,'20'),
          ([826,598,66,73],'Aragosta vino Vermentino di Sardegna 75 cl',[838,703,54,37],3.99,'20'),
          ([1123,598,53,74],'General detersivo liquido lavatrice 44 lavaggi',[1129,703,52,37],2.89,'20')]:add(box,name,pb,price,validFrom='2026-09-'+day,validTo='2026-09-'+day)
    corrections={6:{18:[630,832,49,37],28:[132,1161,48,43],29:[298,1160,46,44]},7:{8:[131,303,48,55],16:[463,483,50,47],27:[132,823,45,45]},10:{10:[798,323,48,38]},14:{33:[795,813,48,58],41:[854,1047,102,30]}}
    corrections[11]={46:[961,1146,50,60]}
    corrections[4]={5:[960,148,48,44],8:[797,316,49,45],15:[464,475,46,57],25:[797,825,46,47],27:[1128,833,49,42]}
    for index,rect in corrections.get(page,{}).items():out[index-1]['caption']=rect
    if page==11:out[45].update(name='Heinz Tomato Ketchup Top Down 625 g',price=1.49)
    if page==4:
        labels=[('Recla prosciutto cotto Praga',.79),('Mec Palmieri mortadella Favola',1.49),('AIA Aequilibrium petto di tacchino cotto al forno',.99),('Rovagnati Gran Biscotto Deli',1.69),('Sa.No. guanciale amatriciano',1.69),('Rigamonti bresaola punta d’anca I.G.P.',3.29),('Casa Montorsi culatta',2.29),('Senfter porchetta di montagna',.99),('Sorrentino salame corallina',.99),('Sorrentino salame tipo Aquila',1.59),('Fiorucci salame spianata romana/piccante',1.49),('Santa Maria Pompea formaggio di mucca',1.29),('Negroni salamino Negronetto',1.59),('Cuor di Maremma pecorino',1.89),('CLAI salamella 100% italiana',1.49),('Central formaggio pecorino Bonsardo',1.69),('Levoni salame Milano/Ungherese',2.69),('Central pecorino pastore',2.19),('Golfera Golfetta',1.99),('Lattebusche formaggio Piave D.O.P. mezzano',1.49),('Toma piemontese D.O.P.',1.09),('CAO formaggio pecorino al peperoncino',1.89),('Boccea Ciumachella di capra',1.69),('CAO formaggio Pastorino sardo',1.79),('Margio Maasdam Olanda',.79),('Latterie Vicentine Bastardo del Montegrappa',1.49),('Pecorella mista',1.49),('Martarelli pecorino nero di grotta',1.99),('Santa Maria caciotta Sienetta mista',1.39),('PLAC provolone piccante Sigillo Rosso',1.29),('Auricchio provolone dolce',1.29),('Toniolo Casearia Montasio D.O.P.',1.29),('Buoni Sapori fiordilatte',.89),('Andriese scamorza bianca/affumicata',1.49),('Maiullari cacio affumicato',.99)]
        for r,(name,price) in zip(out,labels):r.update(name=name,price=price,format='l’etto')
    return out
