import { test, expect, Page } from '@playwright/test';
const BASE=process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const answer='Your friend\'s praise is not evidence. Build the smallest version and put it in front of one potential user before announcing it again. '.repeat(4).trim();
async function setup(page:Page, mode='normal') {
  await page.addInitScript(()=>localStorage.setItem('miryn_token','isolated-browser-test'));
  await page.route('http://localhost:8000/**', async route=> {
    const path=new URL(route.request().url()).pathname;
    if(path==='/chat/stream') {
      if(mode==='wait') await new Promise(r=>setTimeout(r,1800));
      const frames=mode==='error'? [{chunk:'DO NOT DISPLAY'}, {error:'Synthetic server error'}] : [{chunk:answer.slice(0,30)},{chunk:answer.slice(30)},{done:true,conversation_id:'isolated-test'}];
      return route.fulfill({contentType:'text/event-stream',body:frames.map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});
    }
    if(path==='/chat/history') return route.fulfill({json:[{role:'user',content:'Fictional product review.'},{role:'assistant',content:answer}]});
    if(path==='/auth/me') return route.fulfill({json:{id:'test',email:'test@example.invalid',full_name:'UI Review'}});
    if(path==='/memory/'||path==='/memory') return route.fulfill({json:{facts:[],recent:[],emotions:[]}});
    if(path==='/chat/events/stream') return route.fulfill({body:'',contentType:'text/event-stream'});
    return route.fulfill({json:[]});
  });
  await page.goto(BASE+'/chat');
  await page.getByRole('textbox',{name:'Message Miryn'}).fill('Fictional product review.');
  await page.getByRole('button',{name:'Send message'}).click();
}

test('finished response reveals progressively and then completes',async({page}, testInfo)=>{
  await page.emulateMedia({reducedMotion:'no-preference'});
  await setup(page);
  await expect(page.locator('.chat-stream-cursor')).toBeVisible();
  await expect(page.getByRole('button',{name:'Stop generating'})).toBeVisible();
  const partial=await page.locator('main').last().innerText();
  expect(partial).not.toContain(answer);
  await page.screenshot({path:testInfo.outputPath('miryn-reveal-desktop-partial.png')});
  await expect(page.getByRole('button',{name:'Copy response'})).toBeVisible();
  await expect(page.locator('main').last()).toContainText(answer);
  await expect(page.locator('.prose')).toHaveText(answer);
  await page.screenshot({path:testInfo.outputPath('miryn-reveal-desktop-complete.png')});
  await expect(page).toHaveURL(/id=isolated-test/);
  await page.reload();
  await expect(page.locator('.prose')).toHaveText(answer);
  await expect(page.getByRole('button',{name:'Copy response'})).toHaveCount(1);
});

test('Stop cancels animation',async({page}, testInfo)=>{
  await page.emulateMedia({reducedMotion:'no-preference'}); await setup(page);
  await expect(page.locator('.chat-stream-cursor')).toBeVisible();
  await page.getByRole('button',{name:'Stop generating'}).click();
  await expect(page.getByText('Reply stopped. The full reply may already be saved; reopen this chat to see it.')).toBeVisible();
  const text=await page.locator('main').last().innerText();
  await page.waitForTimeout(250); // verify cancelled animation does not continue
  expect(await page.locator('main').last().innerText()).toBe(text);
});

test('navigation cancels reveal without contaminating new chat',async({page}, testInfo)=>{
  await page.emulateMedia({reducedMotion:'no-preference'}); await setup(page);
  await expect(page.locator('.chat-stream-cursor')).toBeVisible();
  await page.getByRole('button',{name:'New chat',exact:true}).click();
  await expect(page.getByRole('heading',{name:'What can I help with today?'})).toBeVisible();
  await page.waitForTimeout(250);
  await expect(page.locator('main').last()).not.toContainText("Your friend's praise");
});

test('server error never reveals buffered chunks',async({page}, testInfo)=>{
  await setup(page,'error');
  await expect(page.getByText('Synthetic server error')).toBeVisible();
  await expect(page.locator('body')).not.toContainText('DO NOT DISPLAY');
});

test('waiting state and reduced-motion mobile completion',async({page}, testInfo)=>{
  await page.setViewportSize({width:390,height:844});
  await page.emulateMedia({reducedMotion:'reduce'}); await setup(page,'wait');
  await expect(page.getByRole('button',{name:'Stop generating'})).toBeVisible();
  await expect(page.locator('.chat-stream-cursor')).toHaveCount(0);
  await page.screenshot({path:testInfo.outputPath('miryn-reveal-mobile-waiting.png')});
  await expect(page.getByRole('button',{name:'Copy response'})).toBeVisible();
  await expect(page.locator('main').last()).toContainText(answer);
  await page.screenshot({path:testInfo.outputPath('miryn-reveal-mobile-complete.png')});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(390);
});
