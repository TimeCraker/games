const http=require('http'),fs=require('fs'),path=require('path');
const PUB=path.join(__dirname,'..','public');
const MIME={'.html':'text/html','.css':'text/css','.js':'application/javascript','.jpg':'image/jpeg','.png':'image/png','.webp':'image/webp','.webmanifest':'application/manifest+json'};
const srv=http.createServer((q,s)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p==='/')p='/index.html';fs.readFile(path.join(PUB,p),(e,d)=>{if(e){s.writeHead(404);s.end();return;}s.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'});s.end(d);});});
srv.listen(8245,async()=>{
  const {execSync}=require('child_process');
  const dir='docs/perf/baseline';fs.mkdirSync(dir,{recursive:true});
  const url='http://localhost:8245/?v=baseline';
  try{
    const out=execSync(`npx --yes lighthouse "${url}" --output=json --output-path=${dir}/lh.json --preset=desktop --chrome-flags="--headless --no-sandbox --disable-gpu" --quiet`,{stdio:'pipe',timeout:180000});
    const lh=JSON.parse(fs.readFileSync(`${dir}/lh.json`,'utf8'));
    const cat=lh.categories;
    console.log('Lighthouse Desktop baseline:');
    console.log('  Performance:',Math.round((cat.performance?.score||0)*100));
    console.log('  LCP:',lh.audits['largest-contentful-paint']?.displayValue);
    console.log('  CLS:',lh.audits['cumulative-layout-shift']?.displayValue);
    console.log('  TBT:',lh.audits['total-blocking-time']?.displayValue);
    console.log('  FCP:',lh.audits['first-contentful-paint']?.displayValue);
  }catch(e){console.error('LH failed:',e.message?.slice(0,200));}
  srv.close();process.exit(0);
});
