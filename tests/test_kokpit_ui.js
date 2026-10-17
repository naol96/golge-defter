// No browser/network dependency: verify display precision and evidence labels.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
function ui() {
  const elements = new Map();
  const element = (id) => {
    if (!elements.has(id)) elements.set(id, {innerHTML:'',textContent:'',children:[],
      setAttribute(k,v){this[k]=v;},addEventListener(event,fn){this[event]=fn;},append(child){this.children.push(child);}});
    return elements.get(id);
  };
  const root={dataset:{theme:'dark'}};
  const context = {document:{documentElement:root,getElementById:element,querySelectorAll:()=>[],createElement:()=>({})},
    localStorage:{setItem(){}},setInterval(){},URL,fetch:()=>new Promise(()=>{})};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('dashboard/kokpit/app.js','utf8'),context);
  return {context,element,root};
}

test('PnL exact display rounding, grouping and very small signed values',()=>{
  const {context}=ui();
  for(const [raw,expected] of [
    ['-0.2997500000000000000000000000','−0,299750'],['0','0,000000'],
    ['0.199750','0,199750'],['-1E-9','−<0,000001'],['1E-9','<0,000001'],
    ['12345678901234567890.1234567','12.345.678.901.234.567.890,123457'],
    ['9.9999995','10,000000'],['NaN','—'],[null,'—'],
  ]) assert.equal(vm.runInContext(`fmtUsdt(${JSON.stringify(raw)})`,context),expected);
});

test('Shadow table exposes origins, precision, target/actual time and limitations',()=>{
  const {context,element}=ui();
  context.snap={recent_shadow:[{shadow_id:1,symbol:'AVAX-USDT',category:'TECHNICAL_UNEXECUTABLE',
    status:'COMPLETE',horizon_minutes:15,pnl_usdt:'-0.29975',entry_source:'ATK_LIVE_MARKET',
    feed_source:'ATK_LIVE_MARKET',signal_origin:'DEMO',note:'stop_dogrulamasi_sinirli;LATE_EVALUATION',
    target_at:1800000900,evaluated_at:1800001021}]};
  vm.runInContext('renderShadow(snap)',context);
  const html=element('shadow-body').innerHTML;
  for(const text of ['−0,299750','Teknik kayıt','Giriş: ATK_LIVE_MARKET','Sinyal: DEMO','Hedef:','Ölçüm:','stop_dogrulamasi_sinirli','LATE_EVALUATION','risk koruması sayılmaz']) assert(html.includes(text));
});

test('Decision table escapes untrusted explanation and shows signal origin',()=>{
  const {context,element}=ui();
  context.snap={recent_decisions:[{id:1,symbol:'AVAX-USDT',status:'SHADOW_RISK',explanation:'<script>bad</script>',signal_origin:'DEMO'}]};
  vm.runInContext('renderDecisions(snap)',context);
  assert(element('decisions-body').innerHTML.includes('&lt;script&gt;'));
  assert(!element('decisions-body').innerHTML.includes('<script>'));
  assert(element('decisions-body').innerHTML.includes('DEMO'));
  vm.runInContext('renderDecisions({});renderShadow({})',context);
  assert(element('decisions-body').innerHTML.includes('colspan="7"'));
  assert(element('shadow-body').innerHTML.includes('colspan="8"'));
});

test('Local SHA and a supplied transaction URL never become verified chain proof',()=>{
  const {context,element}=ui();
  context.snap={anchor:{sha256:'a'.repeat(64),snowtrace_tx:'https://testnet.snowtrace.io/tx/example',blockchain_verified:true}};
  vm.runInContext('renderChain(snap)',context);
  assert(element('chain-body').innerHTML.includes('Doğrulanmış blockchain kanıtı yok'));
  assert(element('chain-body').children[0].textContent.includes('doğrulanmadı'));
  element('chain-body').children=[];
  context.snap.anchor.snowtrace_tx='javascript:alert(1)';
  vm.runInContext('renderChain(snap)',context);
  assert.equal(element('chain-body').children.length,0);
});

test('Theme switch remains functional',()=>{
  const {element,root}=ui();
  element('theme-toggle').click();
  assert.equal(root.dataset.theme,'light');
  assert.equal(element('theme-toggle')['aria-pressed'],'false');
});
