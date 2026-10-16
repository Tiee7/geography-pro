"""Run against a local static server; needs Playwright and Chromium (see README)."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import urllib.request

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('GEOGRAPHY_TEST_URL', 'http://127.0.0.1:8080')
ARTIFACTS = Path(tempfile.mkdtemp(prefix='geography-responsive-'))
CACHE = {}
PROFILES = [(320, 568), (360, 800), (390, 844), (412, 915), (768, 1024),
            (844, 390), (1024, 768), (1280, 800), (1600, 1000)]

if os.environ.get('GEOGRAPHY_TEST_VIEWPORTS'):
    PROFILES = [tuple(map(int, size.split('x'))) for size in os.environ['GEOGRAPHY_TEST_VIEWPORTS'].split(',')]


def download(url):
    # Fetch real pinned CDN assets through the runtime's standard verified TLS
    # and proxy path. No ignore_https_errors or certificate bypass in Chromium.
    if url not in CACHE:
        with urllib.request.urlopen(url, timeout=40) as response:
            CACHE[url] = (response.read(), response.headers.get('Content-Type', 'application/octet-stream'))
    return CACHE[url]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'),
            args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        for width, height in PROFILES:
            mobile = width < 900
            context = await browser.new_context(viewport={'width': width, 'height': height},
                                                 is_mobile=mobile, has_touch=mobile)
            page = await context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))

            async def remote(route):
                body, content_type = await asyncio.to_thread(download, route.request.url)
                await route.fulfill(body=body, content_type=content_type,
                                    headers={'Access-Control-Allow-Origin': '*'})

            async def scene(route):
                source = (ROOT / 'assets/chapter-01/earth-scene.js').read_text()
                source += '\nwindow.__lessonTest = { camera, controls, state, earthMat, atmo, cloudMesh, bloomPass, earthGroup, cityObjects, graticule, sunRaysGroup, terminatorHolder, timezoneGroup, hourLabelsGroup, rotArrowGroup, tropicsGroup, polesGroup };'
                await route.fulfill(body=source, content_type='application/javascript')

            await page.route('https://**/*', remote)
            await page.route('**/assets/chapter-01/earth-scene.js', scene)
            await page.goto(BASE + '/01-earth-rotation.html', wait_until='networkidle', timeout=90000)
            await page.wait_for_selector('#scene-loading', state='hidden')
            assert await page.evaluate('window.__lessonTest.earthMat.uniforms.uDayMap.value.image.width') == 4096
            assert not await page.locator('#btn-pause').is_disabled()
            await page.locator('#btn-pause').click()
            sim_time = await page.evaluate('window.__lessonTest.state.simTime')
            await page.wait_for_timeout(80)
            assert await page.evaluate('window.__lessonTest.state.simTime') == sim_time
            assert await page.locator('#btn-pause').get_attribute('aria-pressed') == 'true'
            projected = await page.evaluate('window.__lessonTest.camera.fov && document.getElementById("globe-viewport").clientHeight / (window.__lessonTest.camera.position.distanceTo(window.__lessonTest.controls.target) * Math.tan(window.__lessonTest.camera.fov * Math.PI / 360))')
            assert projected >= 140, projected
            await page.screenshot(path=str(ARTIFACTS / f'{width}x{height}.png'))

            async def geometry():
                result = await page.evaluate('''() => {
                  const stage = document.querySelector('.stage').getBoundingClientRect();
                  const canvas = document.getElementById('three-canvas').getBoundingClientRect();
                  return { overflow: document.documentElement.scrollWidth > innerWidth,
                    width: stage.width, height: stage.height,
                    canvasWidth: canvas.width, canvasHeight: canvas.height,
                    aspect: window.__lessonTest.camera.aspect, ratio: stage.width / stage.height };
                }''')
                assert not result['overflow'], result
                assert result['width'] >= 250 and result['height'] >= 240, result
                assert abs(result['canvasWidth'] - result['width']) < 2, result
                assert abs(result['canvasHeight'] - result['height']) < 2, result
                assert abs(result['aspect'] - result['ratio']) < 0.01, result

            await geometry()
            for panel in ['layers', 'cities', 'knowledge', 'data', 'controls']:
                await page.locator('#tab-' + panel).click()
                assert await page.locator('#panel-' + panel).is_visible()
                assert await page.locator('[role=tabpanel]:visible').count() == 1
                assert await page.locator('#tab-' + panel).get_attribute('aria-selected') == 'true'
                await geometry()
            await page.locator('[data-speed="100"]').click()
            assert await page.evaluate('window.__lessonTest.state.speed') == 100
            assert await page.locator('#speed-value').inner_text() == '100×'
            await page.locator('[data-day="172"]').click()
            assert await page.evaluate('window.__lessonTest.state.solarLat') > 23
            await page.locator('#kp-select').select_option('terminator')
            await page.locator('#panel-controls [data-open-panel="knowledge"]').click()
            assert '晨昏圈' in await page.locator('#knowledge-topic').inner_text()
            assert await page.locator('.knowledge-formula').is_hidden()
            assert await page.locator('#kp-body').evaluate('(el)=>el.getBoundingClientRect().width') > 200

            await page.locator('#tab-layers').click()
            layer_objects = {'sun': 'sunRaysGroup', 'terminator': 'terminatorHolder',
                             'graticule': 'graticule', 'timezones': 'timezoneGroup',
                             'hourlabels': 'hourLabelsGroup', 'arrows': 'rotArrowGroup',
                             'tropics': 'tropicsGroup', 'poles': 'polesGroup',
                             'clouds': 'cloudMesh', 'atmosphere': 'atmo'}
            assert not await page.locator('#layer-atmosphere').is_checked()
            for name, obj in layer_objects.items():
                checkbox = page.locator('#layer-' + name)
                before = await checkbox.is_checked()
                await checkbox.set_checked(not before)
                assert await page.evaluate(f'window.__lessonTest.{obj}.visible') == (not before)
                await checkbox.set_checked(before)
            await page.locator('#layer-bloom').check()
            assert await page.evaluate('window.__lessonTest.bloomPass.enabled')
            await page.locator('#layer-bloom').uncheck()

            await page.locator('#tab-cities').click()
            await page.locator('[data-city="newyork"]').check()
            await page.locator('#panel-cities [data-open-panel="data"]').click()
            assert await page.locator('#ctime-newyork').count() == 1
            await page.locator('#tab-cities').click()
            for checkbox in await page.locator('[data-city]').all():
                await checkbox.uncheck()
            await page.locator('#tab-data').click()
            assert await page.locator('.city-empty').is_visible()
            await page.locator('#tab-cities').click()
            await page.locator('[data-city="shanghai"]').check()
            await page.locator('#tab-data').click()
            assert await page.locator('#ctime-shanghai').count() == 1

            await page.locator('[data-view="north"]').click()
            assert await page.evaluate('window.__lessonTest.camera.position.y') > 2
            await page.locator('[data-view="south"]').click()
            assert await page.evaluate('window.__lessonTest.camera.position.y') < -2
            await page.locator('#btn-reset-view').click()

            await page.locator('#btn-focus').click()
            assert await page.locator('.inspector').is_hidden()
            await page.wait_for_timeout(100)
            await geometry()
            await page.locator('.header-help').click()
            await page.wait_for_timeout(100)
            assert await page.locator('#panel-knowledge').is_visible()
            assert await page.locator('.inspector').is_visible()
            assert await page.locator('#tab-knowledge').evaluate('(el)=>el === document.activeElement')
            await geometry()

            if width == 390:
                # Real Chromium touch input, not synthetic DOM change events.
                client = await context.new_cdp_session(page)
                box = await page.locator('#three-canvas').bounding_box()
                x, y = box['width'] / 2, box['y'] + box['height'] / 2
                camera_before = await page.evaluate('window.__lessonTest.camera.position.toArray()')
                await client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
                await client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + 55, 'y': y + 10}]})
                await client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                await page.wait_for_timeout(150)
                camera_after = await page.evaluate('window.__lessonTest.camera.position.toArray()')
                assert sum(abs(a-b) for a,b in zip(camera_before, camera_after)) > 0.05
                distance_before = await page.evaluate('window.__lessonTest.camera.position.distanceTo(window.__lessonTest.controls.target)')
                await client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x-25, 'y': y, 'id': 0}, {'x': x+25, 'y': y, 'id': 1}]})
                await client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x-45, 'y': y, 'id': 0}, {'x': x+45, 'y': y, 'id': 1}]})
                await client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                await page.wait_for_timeout(150)
                distance_after = await page.evaluate('window.__lessonTest.camera.position.distanceTo(window.__lessonTest.controls.target)')
                assert distance_after < distance_before - .05
                await page.set_viewport_size({'width': 844, 'height': 390})
                await page.wait_for_timeout(150)
                await geometry()
                await page.set_viewport_size({'width': width, 'height': height})
                await page.wait_for_timeout(150)
                await geometry()
            if not mobile:
                await page.locator('#tab-controls').focus()
                await page.keyboard.press('ArrowRight')
                assert await page.locator('#tab-layers').get_attribute('aria-selected') == 'true'
                await page.keyboard.press('End')
                assert await page.locator('#tab-data').get_attribute('aria-selected') == 'true'
            assert not errors, errors
            print(json.dumps({'viewport': f'{width}x{height}', 'result': 'passed'}, ensure_ascii=False), flush=True)
            await context.close()
        await browser.close()
    print(f'Screenshots: {ARTIFACTS}')


asyncio.run(main())
