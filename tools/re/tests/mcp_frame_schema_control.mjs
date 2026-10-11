import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {pathToFileURL} from 'node:url';
const [sdk,input]=process.argv.slice(2);const {AjvJsonSchemaValidator}=await import(pathToFileURL(path.join(sdk,'node_modules/@modelcontextprotocol/client/dist/validators/ajv.mjs')));
const d=JSON.parse(fs.readFileSync(input));const check=new AjvJsonSchemaValidator().getValidator(d.schema);
assert.equal(check(d.present).valid,true);assert.equal(check(d.absent).valid,true);
const cases=d.cases.map(c=>({kind:c.kind,valid:check(c.content).valid}));
assert.deepEqual(cases.map(c=>c.valid),[false,false,false,false,true,true,false,false]);
process.stdout.write(JSON.stringify({validator:'Official SDK2.3.1 default Node AJV',present:true,absent:true,cases})+'\n');
