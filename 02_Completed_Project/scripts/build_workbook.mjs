import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

// Run from the project folder with the bundled Node runtime.
const root = process.cwd();
const outputDir = path.join(root, 'output');
const qaDir = path.join(root, 'artifacts', 'workbook_qa');
await fs.mkdir(outputDir, {recursive:true});
await fs.mkdir(qaDir, {recursive:true});
const source = JSON.parse(await fs.readFile(path.join(root,'artifacts','workbook_equity_inputs.json'),'utf8'));
const optionResult = JSON.parse(await fs.readFile(path.join(root,'artifacts','options_results.json'),'utf8'));
const manifest = JSON.parse(await fs.readFile(path.join(root,'data','source_manifest.json'),'utf8'));
const prices = source.prices;
const results = source.results;
const options = optionResult.observations ?? optionResult.contracts ?? optionResult.options;
if (!prices?.length || !options?.length) throw new Error('Missing populated price or observed-option inputs');
const assets = ['HDFCBANK','ICICIBANK','SBIN','BAJFINANCE','SHRIRAMFIN','MUTHOOTFIN','NIFTY50'];
const all = [...assets,'BANKS','NBFCS','MIXED'];
const names = ['HDFC Bank','ICICI Bank','State Bank of India','Bajaj Finance','Shriram Finance','Muthoot Finance','NIFTY 50 price','Bank portfolio','NBFC portfolio','50:50 mix'];
const end = prices.length + 5;
const first = 7;
const date = x => new Date(x.slice(0,10)+'T00:00:00Z');
const col = n => {let s='';for(;n>0;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const pct = '0.0%;(0.0%);"–"';
const number = '#,##0.00;(#,##0.00);"–"';
const integer = '#,##0;(#,##0);"–"';
const colors = {navy:'#17324D',blue:'#0000FF',green:'#008000',black:'#18212A',muted:'#657486',pale:'#E9EFF5',amber:'#FFF1CC'};
const wb = Workbook.create();
const sheets = Object.fromEntries(['Summary','Assumptions','Daily returns','Wealth','Options','Prices','Option inputs'].map(n=>[n,wb.worksheets.add(n)]));
function setup(sh,lastColumn,lastRow,raw=false){
  sh.showGridLines=false;
  sh.getRange(`A1:${lastColumn}${lastRow}`).format.font={name:'Arial',size:10,color:colors.black};
  sh.getRange(`A1:${lastColumn}${lastRow}`).format.verticalAlignment='center';
  sh.getRange(`A1:${lastColumn}${lastRow}`).format.rowHeight=19;
  sh.getRange(`A1:${lastColumn}${lastRow}`).format.columnWidth=14;
  if(!raw){sh.getRange(`A1:B${lastRow}`).format.columnWidth=2.5;sh.getRange(`C1:C${lastRow}`).format.columnWidth=25;}
}
function title(sh,cell,text){sh.getRange(cell).values=[[text]];sh.getRange(cell).format.font={name:'Arial',size:15,bold:true,color:colors.navy};sh.getRange(cell).format.rowHeight=27;}
function header(sh,range,vals){sh.getRange(range).values=[vals];sh.getRange(range).format={fill:colors.navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:33};}
function note(sh,cell,text){sh.getRange(cell).values=[[text]];sh.getRange(cell).format.font={name:'Arial',size:10,italic:true,color:colors.muted};}
function formulas(sh,range,matrix,cross=true){sh.getRange(range).formulas=matrix;sh.getRange(range).format.font.color=cross?colors.green:colors.black;}
function block(sh,cell,text){sh.getRange(cell).values=[[text]];sh.getRange(cell).format.font.bold=true;sh.getRange(cell).format.font.color=colors.navy;}

const assumptions=sheets.Assumptions;
setup(assumptions,'L',30);
assumptions.tabColor='#56718B';
title(assumptions,'C2','Assumptions and portfolio weights');
header(assumptions,'C5:E5',['Setting','Value','Definition']);
assumptions.getRange('C6:E13').values=[
  ['Annual risk-free rate',0.06,'Effective annual assumption; constant through the sample'],
  ['Trading days per year',252,'Annualization convention'],
  ['Initial wealth',100,'Index units at the base close'],
  ['Option days per year',365,'Calendar time convention'],
  ['CAGR days per year',365.25,'Calendar-day annualization'],
  ['Daily risk-free return',null,'Converted from the effective annual rate'],
  ['Option continuous rate',null,'Natural logarithm of 1 + effective annual rate'],
  ['Continuous dividend yield',0,'Baseline assumption for both option underlyings']
];
assumptions.getRange('D6:D10').format.font.color=colors.blue;
assumptions.getRange('D13').format.font.color=colors.blue;
assumptions.getRange('D6:D10').format.fill=colors.amber;
assumptions.getRange('D13').format.fill=colors.amber;
formulas(assumptions,'D11:D12',[['=(1+D6)^(1/D7)-1'],['=LN(1+D6)']],false);
assumptions.getRange('D6').setNumberFormat(pct);
assumptions.getRange('D11:D13').setNumberFormat('0.0000%');
assumptions.getRange('E5:E13').format.columnWidth=68;
assumptions.getRange('C6:C13').format.columnWidth=31;
header(assumptions,'C18:J18',['Portfolio',...assets.slice(0,6),'Weight sum']);
assumptions.getRange('C19:I21').values=[['BANKS',1/3,1/3,1/3,0,0,0],['NBFCS',0,0,0,1/3,1/3,1/3],['MIXED',1/6,1/6,1/6,1/6,1/6,1/6]];
assumptions.getRange('D19:I21').format.font.color=colors.blue;
assumptions.getRange('D19:I21').setNumberFormat(pct);
formulas(assumptions,'J19:J21',Array.from({length:3},(_,i)=>[`=SUM(D${19+i}:I${19+i})`]),false);
assumptions.getRange('J19:J21').setNumberFormat(pct);
assumptions.getRange('J19:J21').conditionalFormats.add('cellIs',{operator:'notEqual',formula:1,format:{fill:'#FCE4E4',font:{color:'#A00000',bold:true}}});
note(assumptions,'C24','Constant weights imply daily rebalancing. Returns exclude transaction costs, tax, spreads and slippage.');
note(assumptions,'C26','Blue cells are inputs. Green formulas link other sheets. Black formulas calculate within a sheet.');
note(assumptions,'C28','Rates and portfolio weights are assumptions. Price and option observations remain unchanged when these are edited.');

const pr=sheets.Prices;
setup(pr,'K',end,true);
title(pr,'A2','Adjusted daily equity prices and price-index benchmark');
note(pr,'A3','Equities use vendor dividend/split-adjusted close (INR). NIFTY 50 is a price index (points).');
header(pr,'A5:H5',['Date',...assets]);
pr.getRange(`A6:H${end}`).values=prices.map(p=>[date(p.date),...assets.map(a=>Number(p[a]))]);
pr.getRange(`A6:A${end}`).setNumberFormat('dd-mmm-yy');
pr.getRange(`B6:H${end}`).setNumberFormat(number);
pr.getRange(`B6:H${end}`).format.font.color=colors.blue;
pr.getRange(`A1:A${end}`).format.columnWidth=14;
pr.freezePanes.freezeRows(5);
pr.freezePanes.freezeColumns(1);
header(pr,'J5:K5',['Input series','Source URL and basis']);
pr.getRange('J6:K12').values=manifest.sources.map(s=>[s.symbol,s.url]);
pr.getRange('J1:J15').format.columnWidth=19;
pr.getRange('K1:K15').format.columnWidth=115;
note(pr,'J14','Provider: Yahoo Finance. Raw responses and retrieval checksums are included in the project data folder.');
note(pr,'J16','Already-adjusted values: do not apply corporate-action factors again. Shriram includes its listed predecessor.');

const ret=sheets['Daily returns'];
setup(ret,'K',end,true);
title(ret,'A2','Daily returns');
note(ret,'A3','Simple adjusted-price returns. The initial close has no return. Portfolio rows use the common aligned dates.');
header(ret,'A5:K5',['Date',...all]);
formulas(ret,`A6:A${end}`,prices.map((_,i)=>[`='Prices'!A${i+6}`]));
formulas(ret,`B7:H${end}`,prices.slice(1).map((_,i)=>assets.map((a,j)=>`='Prices'!${col(j+2)}${i+7}/'Prices'!${col(j+2)}${i+6}-1`)));
formulas(ret,`I7:K${end}`,prices.slice(1).map((_,i)=>[19,20,21].map(w=>`=SUMPRODUCT(B${i+7}:G${i+7},'Assumptions'!$D$${w}:$I$${w})`)));
ret.getRange(`A6:A${end}`).setNumberFormat('dd-mmm-yy');
ret.getRange(`B7:K${end}`).setNumberFormat('0.00%;(0.00%);"–"');
ret.freezePanes.freezeRows(5);ret.freezePanes.freezeColumns(1);

const wealth=sheets.Wealth;
setup(wealth,'V',end,true);
title(wealth,'A2','Wealth and drawdown');
note(wealth,'A3','Wealth compounds each daily return. Drawdown equals wealth divided by the running peak, less one.');
header(wealth,'A5:K5',['Date',...all]);
header(wealth,'M5:V5',all.map(a=>a+' drawdown'));
formulas(wealth,`A6:A${end}`,prices.map((_,i)=>[`='Prices'!A${i+6}`]));
formulas(wealth,'B6:K6',[all.map(()=>"='Assumptions'!$D$8")]);
formulas(wealth,`B7:K${end}`,prices.slice(1).map((_,i)=>all.map((a,j)=>`=${col(j+2)}${i+6}*(1+'Daily returns'!${col(j+2)}${i+7})`)));
formulas(wealth,`M6:V${end}`,prices.map((_,i)=>all.map((a,j)=>`=${col(j+2)}${i+6}/MAX(${col(j+2)}$6:${col(j+2)}${i+6})-1`)),false);
wealth.getRange(`A6:A${end}`).setNumberFormat('dd-mmm-yy');
wealth.getRange(`B6:K${end}`).setNumberFormat(number);
wealth.getRange(`M6:V${end}`).setNumberFormat(pct);
wealth.getRange(`L1:L${end}`).format.columnWidth=3;
wealth.freezePanes.freezeRows(5);wealth.freezePanes.freezeColumns(1);

const summary=sheets.Summary;
setup(summary,'W',46);
summary.tabColor=colors.navy;
title(summary,'C2','Risk and return of Indian financial stocks');
note(summary,'C3','2021–2025. Six selected equities and three daily-rebalanced portfolios. Equity returns include vendor dividend adjustments.');
header(summary,'C6:M6',['Instrument','Days','Total return','CAGR','Ann. mean','Ann. volatility','Sharpe','Beta','Max drawdown','Daily VaR 95%','Daily CVaR 95%']);
summary.getRange('C7:C16').values=names.map(n=>[n]);
const metricFormulas=all.map((a,j)=>{
 const c=col(j+2), r=j+7, rs=`'Daily returns'!${c}$${first}:${c}$${end}`, dd=`'Wealth'!${col(j+13)}$6:${col(j+13)}$${end}`;
 return [`=COUNT(${rs})`,`='Wealth'!${c}${end}/'Wealth'!${c}6-1`,`=(1+E${r})^('Assumptions'!$D$10/('Prices'!$A$${end}-'Prices'!$A$6))-1`,`=AVERAGE(${rs})*'Assumptions'!$D$7`,`=STDEV.S(${rs})*SQRT('Assumptions'!$D$7)`,`=(AVERAGE(${rs})-'Assumptions'!$D$11)/STDEV.S(${rs})*SQRT('Assumptions'!$D$7)`,`=SLOPE(${rs},'Daily returns'!$H$${first}:$H$${end})`,`=MIN(${dd})`,`=-PERCENTILE.INC(${rs},0.05)`,`=-AVERAGEIFS(${rs},${rs},"<="&(-L${r}))`];
});
summary.getRange('D7:M16').formulas=metricFormulas;
summary.getRange('E7:H16').setNumberFormat(pct);summary.getRange('K7:M16').setNumberFormat(pct);
summary.getRange('I7:J16').setNumberFormat('0.00');summary.getRange('D7:D16').setNumberFormat(integer);
summary.getRange('C14:M16').format.fill=colors.pale;
summary.getRange('D1:D46').format.columnWidth=9;
summary.getRange('E1:M46').format.columnWidth=13;
summary.getRange('C1:C46').format.columnWidth=24;
note(summary,'C18','Beta uses NIFTY 50 price returns. Dividend-adjusted stocks and the price index are not a like-for-like performance benchmark.');
header(summary,'C21:M21',['Calendar year',...all]);
const years=[2021,2022,2023,2024,2025];
const yearEnd=[0,...years.map(y=>prices.findLastIndex(p=>p.date.startsWith(String(y))))];
summary.getRange('C22:C26').values=years.map(y=>[y]);
summary.getRange('D22:M26').formulas=years.map((y,i)=>all.map((a,j)=>`='Wealth'!${col(j+2)}${yearEnd[i+1]+6}/'Wealth'!${col(j+2)}${yearEnd[i]+6}-1`));
summary.getRange('D22:M26').setNumberFormat(pct);
header(summary,'C30:I30',['Return correlation',...assets.slice(0,6)]);
summary.getRange('C31:C36').values=assets.slice(0,6).map(a=>[a]);
summary.getRange('D31:I36').formulas=assets.slice(0,6).map((a,i)=>assets.slice(0,6).map((b,j)=>`=CORREL('Daily returns'!${col(i+2)}${first}:${col(i+2)}${end},'Daily returns'!${col(j+2)}${first}:${col(j+2)}${end})`));
summary.getRange('D31:I36').setNumberFormat('0.00');
summary.getRange('D31:I36').conditionalFormats.add('colorScale',{colors:['#FFFFFF','#8BACBF'],thresholds:[0,1]});
header(summary,'C39:F39',['Year-end wealth','Banks','NBFCs','50:50 mix']);
summary.getRange('C40:C45').values=[['Base 2020'],...years.map(y=>[String(y)])];
summary.getRange('D40:F45').formulas=yearEnd.map(i=>[9,10,11].map(j=>`='Wealth'!${col(j)}${i+6}`));
summary.getRange('D40:F45').setNumberFormat(number);
block(summary,'H40','Diversification reduction');
summary.getRange('H41').values=[['Volatility vs weighted average']];
summary.getRange('K41').formulas=[['=(0.5*H14+0.5*H15)-H16']];
summary.getRange('K41').setNumberFormat(pct);
note(summary,'H43','Percentage-point reduction; it need not beat both stand-alone volatilities.');
const chart=summary.charts.add('line',summary.getRange('C39:F45'));
chart.title='Portfolio wealth at calendar year-end (base 100)';
chart.setPosition('O5','W22');
chart.titleTextStyle.fontSize=13;chart.titleTextStyle.typeface='Arial';
chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};
chart.yAxis={numberFormatCode:'0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};
chart.legend={position:'bottom',textStyle:{typeface:'Arial',fontSize:10}};
['#275D8A','#D88435','#399478'].forEach((c,i)=>{chart.series.items[i].line={fill:c,style:'solid',width:2};chart.series.items[i].fill=c;});
const comparison=summary.charts.add('bar',[summary.getRange('C13:C16'),summary.getRange('I13:I16')]);
comparison.title='Realized Sharpe ratio';comparison.setPosition('O25','W40');
comparison.titleTextStyle.typeface='Arial';comparison.titleTextStyle.fontSize=13;
comparison.hasLegend=false;comparison.series.items[0].fill='#275D8A';
comparison.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};
comparison.yAxis={numberFormatCode:'0.00',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};

// Contracts remain observed input rows. Black-Scholes intermediate calculations stay visible.
const input=sheets['Option inputs'];
setup(input,'Q',15,true);
title(input,'A2','Observed option contracts');
note(input,'A3','31 December 2025 NSE closing premiums. Spot is the contemporaneous unadjusted exchange share price.');
header(input,'A5:M5',['Symbol','Type','Valuation date','Expiry date','Spot INR','Strike INR','Premium INR','Volume contracts','Open interest (contracts)','Historical vol','Implied vol','Source archive URL','Premium type']);
const rows=options.map(o=>[
 o.symbol??o.ticker,o.option_type??o.type,date(o.valuation_date??o.date),date(o.expiry_date??o.expiry),
 o.spot,o.strike,o.market_price??o.market_premium??o.close,o.volume??o.volume_contracts,o.open_interest_contracts,
 o.historical_volatility??o.sigma_historical??o.hist_vol,o.implied_volatility??o.implied_vol??o.derived_iv,
 o.source_url??optionResult.source_url??'',o.premium_type??'Close'
]);
input.getRange(`A6:M${5+rows.length}`).values=rows;
input.getRange(`C6:D${5+rows.length}`).setNumberFormat('dd-mmm-yy');
input.getRange(`E6:G${5+rows.length}`).setNumberFormat(number);
input.getRange(`H6:I${5+rows.length}`).setNumberFormat(integer);
input.getRange(`J6:K${5+rows.length}`).setNumberFormat(pct);
input.getRange(`E6:K${5+rows.length}`).format.font.color=colors.blue;
input.getRange('A1:A15').format.columnWidth=17;input.getRange('B1:B15').format.columnWidth=9;
input.getRange('L1:L15').format.columnWidth=104;
note(input,'A12','Historical volatility is sample SD of the trailing 252 daily simple adjusted returns, annualized by sqrt(252).');
note(input,'A14','Implied volatility is numerically inverted from each observed premium. Its repricing is a calibration check, not independent validation.');

const op=sheets.Options;
setup(op,'O',35);
title(op,'C2','Black–Scholes option valuation');
note(op,'C3','Four observed contracts. Calendar days/365; constant rate and volatility; continuous dividend-yield assumption.');
header(op,'C5:G5',['Input or result',...rows.map(r=>`${r[0]} ${r[1]}`)]);
op.getRange('C6:C30').values=[['Spot (INR)'],['Strike (INR)'],['Time to expiry (years)'],['Historical volatility'],['Continuous risk-free rate'],['Dividend yield'],['Observed premium (INR)'],['d1'],['d2'],['N(d1)'],['N(d2)'],['Normal density at d1'],['Model premium (INR)'],['Model minus observed'],['Difference / observed'],['Delta'],['Gamma'],['Vega per 1 vol point'],['Derived implied volatility'],['Model at implied volatility'],['IV repricing residual'],['Historical vol lookback'],['Valuation date'],['Expiry date'],['Option type']];
rows.forEach((o,j)=>{
 const c=col(j+4),ir=j+6,assetCol=col(assets.indexOf(o[0])+2);
 const f=[`='Option inputs'!E${ir}`,`='Option inputs'!F${ir}`,`=('Option inputs'!D${ir}-'Option inputs'!C${ir})/'Assumptions'!$D$9`,`=STDEV.S('Daily returns'!${assetCol}${end-251}:${assetCol}${end})*SQRT('Assumptions'!$D$7)`,`='Assumptions'!$D$12`,`='Assumptions'!$D$13`,`='Option inputs'!G${ir}`,
 `=(LN(${c}6/${c}7)+(${c}10-${c}11+${c}9^2/2)*${c}8)/(${c}9*SQRT(${c}8))`,`=${c}13-${c}9*SQRT(${c}8)`,`=NORM.S.DIST(${c}13,TRUE)`,`=NORM.S.DIST(${c}14,TRUE)`,`=NORM.S.DIST(${c}13,FALSE)`,
 `=IF(${c}30="CE",${c}6*EXP(-${c}11*${c}8)*${c}15-${c}7*EXP(-${c}10*${c}8)*${c}16,${c}7*EXP(-${c}10*${c}8)*(1-${c}16)-${c}6*EXP(-${c}11*${c}8)*(1-${c}15))`,`=${c}18-${c}12`,`=${c}19/${c}12`,`=IF(${c}30="CE",EXP(-${c}11*${c}8)*${c}15,EXP(-${c}11*${c}8)*(${c}15-1))`,`=EXP(-${c}11*${c}8)*${c}17/(${c}6*${c}9*SQRT(${c}8))`,`=${c}6*EXP(-${c}11*${c}8)*${c}17*SQRT(${c}8)/100`,`='Option inputs'!K${ir}`,null,null,`='Assumptions'!$D$7`,`='Option inputs'!C${ir}`,`='Option inputs'!D${ir}`,`='Option inputs'!B${ir}`];
 op.getRange(`${c}6:${c}30`).formulas=f.map(x=>[x]);
 const di=`(LN(${c}6/${c}7)+(${c}10-${c}11+${c}24^2/2)*${c}8)/(${c}24*SQRT(${c}8))`;
 const de=`(${di}-${c}24*SQRT(${c}8))`;
 op.getRange(`${c}25`).formulas=[[`=IF(${c}30="CE",${c}6*EXP(-${c}11*${c}8)*NORM.S.DIST(${di},TRUE)-${c}7*EXP(-${c}10*${c}8)*NORM.S.DIST(${de},TRUE),${c}7*EXP(-${c}10*${c}8)*NORM.S.DIST(-${de},TRUE)-${c}6*EXP(-${c}11*${c}8)*NORM.S.DIST(-${di},TRUE))`]];
 op.getRange(`${c}26`).formulas=[[`=${c}25-${c}12`]];
});
op.getRange('C1:C35').format.columnWidth=31;
op.getRange('D1:G35').format.columnWidth=22;
op.getRange('D6:G26').setNumberFormat(number);
op.getRange('D8:G8').setNumberFormat('0.00000');op.getRange('D9:G11').setNumberFormat('0.00%');
op.getRange('D20:G20').setNumberFormat('0.0%;(0.0%);"–"');op.getRange('D21:G22').setNumberFormat('0.0000');op.getRange('D24:G24').setNumberFormat('0.00%');
op.getRange('D28:G29').setNumberFormat('dd-mmm-yy');
op.getRange('C18:G18').format.fill=colors.pale;op.getRange('C21:G23').format.fill=colors.pale;
note(op,'C33','Model-price differences are conditional on the assumptions. They do not establish executable arbitrage or sector-wide mispricing.');
note(op,'C35','Changing the risk-free assumption recalculates prices and Greeks. The stored implied-volatility input is the original-date inversion.');

wb.recalculate();
const check={};
check.summary=JSON.parse(JSON.stringify(summary.getRange('D7:M16').values));
check.option_values=op.getRange('D6:G30').values;
check.observations=prices.length-1;
const originalSharpe=Number(summary.getRange('I14').values[0][0]);
const originalOption=Number(op.getRange('D18').values[0][0]);
assumptions.getRange('D6').values=[[0.08]];
wb.recalculate();
check.rate_change={originalSharpe,newSharpe:Number(summary.getRange('I14').values[0][0]),originalOption,newOption:Number(op.getRange('D18').values[0][0])};
if(check.rate_change.originalSharpe===check.rate_change.newSharpe||check.rate_change.originalOption===check.rate_change.newOption)throw new Error('Rate-input recalculation failed');
assumptions.getRange('D6').values=[[0.06]];
wb.recalculate();
check.restored={sharpe:Number(summary.getRange('I14').values[0][0]),option:Number(op.getRange('D18').values[0][0])};
const inspect=await wb.inspect({kind:'table',range:'Summary!C6:M16',include:'values,formulas',tableMaxRows:11,tableMaxCols:11,maxChars:10000});
await fs.writeFile(path.join(qaDir,'summary_inspect.ndjson'),inspect.ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},summary:'Final formula error scan',maxChars:10000});
await fs.writeFile(path.join(qaDir,'formula_errors.ndjson'),errors.ndjson);
await fs.writeFile(path.join(qaDir,'verification.json'),JSON.stringify(check,null,2));
console.log('Formula scan',errors.ndjson);
for(const [name,range] of [['Summary','C1:M18'],['Assumptions','C2:J28'],['Daily returns','A2:K15'],['Wealth','A2:K15'],['Options','C2:G35'],['Prices','A2:H15'],['Option inputs','A2:K14']]){
 const preview=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
 await fs.writeFile(path.join(qaDir,name.replaceAll(' ','_')+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
const visual=await wb.render({sheetName:'Summary',range:'O3:W41',scale:1.5,format:'png'});
await fs.writeFile(path.join(qaDir,'Summary_charts.png'),new Uint8Array(await visual.arrayBuffer()));
const file=await SpreadsheetFile.exportXlsx(wb);
await file.save(path.join(outputDir,'Risk_Return_Calculations.xlsx'));
console.log(JSON.stringify({output:path.join(outputDir,'Risk_Return_Calculations.xlsx'),observations:check.observations,rate_change:check.rate_change,summary:check.summary,options:check.option_values},null,2));
