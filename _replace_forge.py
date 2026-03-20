#!/usr/bin/env python3
"""Replace old Forge + Smart Forge tabs with unified Forge tab."""
import pathlib

html_path = pathlib.Path("/opt/titan-v11.3-device/console/index.html")
lines = html_path.read_text().splitlines(keepends=True)

# Find markers
forge_start = None
smart_forge_end = None
for i, line in enumerate(lines):
    if "<!-- FORGE -->" in line and forge_start is None:
        forge_start = i
    if "<!-- PROFILES -->" in line:
        smart_forge_end = i
        break

assert forge_start is not None, "Could not find <!-- FORGE -->"
assert smart_forge_end is not None, "Could not find <!-- PROFILES -->"

print(f"Replacing lines {forge_start+1} through {smart_forge_end} (0-indexed: {forge_start}..{smart_forge_end-1})")

NEW_FORGE = r'''  <!-- FORGE (Unified: AI SmartForge + Manual + OSINT + Proxy) -->
  <div x-show="genesisTab==='Forge'">
    <div class="space-y-4">

      <!-- Mode toggle -->
      <div class="flex items-center gap-3 mb-1">
        <span class="text-[10px] text-gray-500 uppercase tracking-wider">Forge Mode:</span>
        <button @click="forgeMode='smart'" class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all" :class="forgeMode==='smart'?'bg-green-900/60 text-green-400 ring-1 ring-green-700':'bg-gray-800 text-gray-500 hover:text-white'">&#x1F9E0; AI Smart Forge</button>
        <button @click="forgeMode='manual'" class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all" :class="forgeMode==='manual'?'bg-cyan-900/60 text-cyan-400 ring-1 ring-cyan-700':'bg-gray-800 text-gray-500 hover:text-white'">&#x270F;&#xFE0F; Manual</button>
        <div class="flex-1"></div>
        <label class="flex items-center gap-2 text-xs text-gray-400"><input type="checkbox" x-model="forge.use_ai" class="rounded"> AI Enrichment</label>
        <label class="flex items-center gap-2 text-xs text-gray-400"><input type="checkbox" x-model="forge.run_osint" class="rounded"> OSINT Recon</label>
      </div>

      <!-- AI SMART FORGE section (shown in smart mode) -->
      <div x-show="forgeMode==='smart'" class="grp glow">
        <h3 class="grp-title text-green-400">&#x1F9E0; AI Smart Forge</h3>
        <p class="text-[11px] text-gray-500 mb-3">Provide occupation, country, age &#8212; AI generates a complete persona. Override any field below.</p>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div><label class="lbl">Occupation</label><select x-model="forge.occupation" class="inp"><option value="auto">Auto</option><option value="software_engineer">Software Engineer</option><option value="doctor">Doctor</option><option value="teacher">Teacher</option><option value="retiree">Retiree</option><option value="gamer">Gamer</option><option value="freelancer">Freelancer</option><option value="student">Student</option><option value="small_business_owner">Small Business</option><option value="government_worker">Government Worker</option><option value="retail_worker">Retail Worker</option></select></div>
          <div><label class="lbl">Country</label><select x-model="forge.country" class="inp"><option value="US">United States</option><option value="GB">United Kingdom</option><option value="CA">Canada</option><option value="AU">Australia</option><option value="DE">Germany</option><option value="FR">France</option><option value="NL">Netherlands</option><option value="IT">Italy</option><option value="ES">Spain</option><option value="BE">Belgium</option><option value="JP">Japan</option><option value="BR">Brazil</option><option value="MX">Mexico</option></select></div>
          <div><label class="lbl">Age</label><input type="number" x-model.number="forge.persona_age" min="18" max="80" class="inp"></div>
          <div><label class="lbl">Gender</label><select x-model="forge.gender" class="inp"><option value="auto">Auto</option><option value="M">Male</option><option value="F">Female</option></select></div>
          <div><label class="lbl">Target Site</label><input type="text" x-model="forge.target" placeholder="amazon.com" class="inp"></div>
        </div>
      </div>

      <!-- IDENTITY (always shown - in smart mode these are overrides, in manual mode they are primary) -->
      <div class="grp" :class="forgeMode==='smart'?'':'glow'">
        <div class="flex items-center justify-between cursor-pointer" @click="forgeIdentityOpen=!forgeIdentityOpen">
          <h3 class="grp-title mb-0" :class="forgeMode==='smart'?'text-cyan-400':'text-green-400'" x-text="forgeMode==='smart'?'Identity Override (optional)':'Identity'"></h3>
          <span class="text-gray-500 text-xs" x-text="forgeIdentityOpen?'\u25BC':'\u25B6'"></span>
        </div>
        <div x-show="forgeIdentityOpen || forgeMode==='manual'" class="mt-3 space-y-3">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="md:col-span-2"><label class="lbl">Full Name</label><input type="text" x-model="forge.name" placeholder="Full name" class="inp"></div>
            <div><label class="lbl">DOB (DD/MM/YYYY)</label><input type="text" x-model="forge.dob" placeholder="DD/MM/YYYY" class="inp"></div>
            <div><label class="lbl">Phone Number</label><input type="text" x-model="forge.phone" placeholder="Phone number" class="inp"></div>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div><label class="lbl">Email</label><input type="text" x-model="forge.email" placeholder="Auto from name" class="inp"></div>
            <div><label class="lbl">National ID (SSN/NIN)</label><input type="text" x-model="forge.ssn" placeholder="National ID" class="inp"></div>
            <div x-show="forgeMode==='manual'"><label class="lbl">Country</label><select x-model="forge.country" class="inp"><option value="US">United States</option><option value="GB">United Kingdom</option><option value="CA">Canada</option><option value="AU">Australia</option><option value="DE">Germany</option><option value="FR">France</option></select></div>
            <div x-show="forgeMode==='manual'"><label class="lbl">Occupation</label><select x-model="forge.occupation" class="inp"><option value="auto">Auto</option><option value="retiree">Retiree</option><option value="software_engineer">Software Engineer</option><option value="doctor">Doctor</option><option value="teacher">Teacher</option><option value="gamer">Gamer</option><option value="freelancer">Freelancer</option><option value="retail_worker">Retail Worker</option><option value="student">Student</option><option value="small_business_owner">Small Business</option></select></div>
          </div>
          <div><label class="lbl">Street Address</label><input type="text" x-model="forge.street" placeholder="Street address" class="inp"></div>
          <div class="grid grid-cols-3 gap-3">
            <div><label class="lbl">City</label><input type="text" x-model="forge.city" placeholder="City" class="inp"></div>
            <div><label class="lbl">State / Region</label><input type="text" x-model="forge.state" placeholder="State" class="inp"></div>
            <div><label class="lbl">Zip / Postcode</label><input type="text" x-model="forge.zip" placeholder="Zip" class="inp"></div>
          </div>
        </div>
      </div>

      <!-- CARD DATA -->
      <div class="grp">
        <h3 class="grp-title text-yellow-400">Payment Card</h3>
        <div class="grid grid-cols-4 gap-3">
          <div><label class="lbl">CC Number</label><input type="text" x-model="forge.cc" placeholder="Card number" class="inp"></div>
          <div><label class="lbl">Expiry (MM/YYYY)</label><input type="text" x-model="forge.cc_exp" placeholder="MM/YYYY" class="inp"></div>
          <div><label class="lbl">CVV</label><input type="text" x-model="forge.cc_cvv" placeholder="CVV" class="inp"></div>
          <div><label class="lbl">Cardholder</label><input type="text" x-model="forge.cc_holder" placeholder="Auto from name" class="inp"></div>
        </div>
      </div>

      <!-- OSINT RECON (shown when toggle is on) -->
      <div x-show="forge.run_osint" class="grp border-purple-800 bg-purple-900/10">
        <h3 class="grp-title text-purple-400">&#x1F50D; OSINT Recon</h3>
        <p class="text-[11px] text-gray-500 mb-3">Sherlock, Maigret, Holehe &#8212; enriches forged persona with real social footprint data.</p>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div><label class="lbl">Name</label><input type="text" x-model="forge.osint_name" placeholder="Target name" class="inp"></div>
          <div><label class="lbl">Email</label><input type="text" x-model="forge.osint_email" placeholder="target@email.com" class="inp"></div>
          <div><label class="lbl">Username</label><input type="text" x-model="forge.osint_username" placeholder="username" class="inp"></div>
          <div><label class="lbl">Phone</label><input type="text" x-model="forge.osint_phone" placeholder="+1-555-123-4567" class="inp"></div>
          <div><label class="lbl">Domain</label><input type="text" x-model="forge.osint_domain" placeholder="example.com" class="inp"></div>
        </div>
        <div class="mt-2 flex items-center gap-3">
          <button @click="checkOsintTools()" class="text-[10px] text-gray-500 hover:text-purple-400">Check Tools</button>
          <span class="text-[10px] text-gray-600" x-text="osintToolsStatus||''"></span>
        </div>
      </div>

      <!-- PROXY CONFIG -->
      <div class="grp">
        <h3 class="grp-title text-orange-400">&#x1F310; Proxy &amp; Network</h3>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="lbl">Proxy (SOCKS5)</label><div class="flex gap-2"><input type="text" x-model="forge.proxy" placeholder="socks5://user:pass@host:port" class="inp flex-1"><button @click="testProxy()" class="btn-secondary text-white px-3 py-1 rounded-lg text-xs">Test</button></div></div>
          <div><label class="lbl">Proxy Status</label><div class="inp bg-[#0f172a] text-xs h-[38px] flex items-center" :class="forge.proxy_status?.startsWith('OK')?'text-green-400':forge.proxy_status?'text-red-400':'text-gray-500'" x-text="forge.proxy_status||'Not tested'"></div></div>
        </div>
      </div>

      <!-- GOOGLE ACCOUNT -->
      <div class="grp" x-data="{open:false}">
        <div class="flex items-center justify-between cursor-pointer" @click="open=!open">
          <h3 class="grp-title text-blue-400 mb-0">&#x1F512; Google Account (Pre-Injection)</h3>
          <span class="text-gray-500 text-xs" x-text="open?'\u25BC':'\u25B6'"></span>
        </div>
        <div x-show="open" class="mt-3 space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div><label class="lbl">Google Email</label><input type="email" x-model="forge.google_email" placeholder="persona@gmail.com" class="inp"></div>
            <div><label class="lbl">Google Password</label><input type="password" x-model="forge.google_password" placeholder="Account password" class="inp"></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="lbl">Real Phone (OTP)</label><div class="flex gap-2"><input type="tel" x-model="forge.real_phone" placeholder="+14304314828" class="inp flex-1"><span class="text-[10px] self-center px-1.5 py-0.5 rounded" :class="forge.otp_status==='received'?'bg-green-900/50 text-green-400':forge.otp_status==='waiting'?'bg-yellow-900/50 text-yellow-400':'bg-gray-700 text-gray-500'" x-text="forge.otp_status||'idle'"></span></div></div>
            <div><label class="lbl">OTP Code</label><div class="flex gap-2"><input type="text" x-model="forge.otp_code" placeholder="Auto or manual" class="inp flex-1" maxlength="6"><button @click="requestOtp()" :disabled="!forge.real_phone" class="btn-secondary text-white px-3 py-1 rounded-lg text-[10px] disabled:opacity-50">Request</button></div></div>
          </div>
        </div>
      </div>

      <!-- DEVICE TARGET & AGING -->
      <div class="grp">
        <h3 class="grp-title text-cyan-400">&#x1F4F1; Device Target</h3>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div><label class="lbl">Target Device</label><select x-model="forge.device_id" class="inp"><option value="">None (forge only)</option><template x-for="d in devices" :key="d.id"><option :value="d.id" x-text="d.id+' ('+presetName(d.config?.model)+')'"></option></template></select></div>
          <div><label class="lbl">Age (days)</label><input type="number" x-model.number="forge.age_days" min="0" max="900" class="inp"></div>
          <div><label class="lbl">Device Model</label><select x-model="forge.device_model" class="inp"><template x-for="p in presets" :key="p.key"><option :value="p.key" x-text="p.name"></option></template></select></div>
          <div><label class="lbl">Carrier</label><select x-model="forge.carrier" class="inp"><template x-for="(c,key) in carriers" :key="key"><option :value="key" x-text="c.name"></option></template></select></div>
          <div><label class="lbl">Location</label><select x-model="forge.location" class="inp"><template x-for="(loc,key) in locations" :key="key"><option :value="key" x-text="key.toUpperCase()"></option></template></select></div>
        </div>
      </div>

      <!-- ACTION BUTTONS -->
      <div class="flex gap-3 flex-wrap">
        <button x-show="forge.device_id" @click="unifiedForgeProvision()" :disabled="forging" class="btn-green text-black px-6 py-3 rounded-lg text-sm font-bold disabled:opacity-50 flex items-center gap-2">
          <span x-show="!forging">&#9889; FORGE + INJECT + PATCH</span>
          <span x-show="forging">Working...</span>
        </button>
        <button @click="unifiedForge(true)" :disabled="forging" class="btn-primary text-white px-6 py-3 rounded-lg text-sm font-bold disabled:opacity-50"><span x-show="!forging" x-text="forge.device_id ? 'FORGE + INJECT' : 'FORGE + INJECT'"></span><span x-show="forging">Working...</span></button>
        <button @click="unifiedForge(false)" :disabled="forging" class="btn-secondary text-white px-6 py-3 rounded-lg text-sm font-bold disabled:opacity-50">FORGE ONLY</button>
        <button @click="previewUnifiedForge()" class="btn-secondary text-white px-4 py-3 rounded-lg text-sm font-bold">PREVIEW</button>
      </div>

      <!-- Provision progress stepper -->
      <div x-show="provisionJob" class="grp border-cyan-800 bg-cyan-900/10">
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-cyan-400 text-xs font-bold uppercase">Provision Pipeline</h4>
          <span class="text-[10px] font-mono" :class="provisionJob?.status==='completed'?'text-green-400':provisionJob?.status==='failed'?'text-red-400':'text-yellow-400'" x-text="provisionJob?.status?.toUpperCase()||''" ></span>
        </div>
        <div class="flex items-center gap-1 text-xs flex-wrap">
          <template x-for="(s,i) in [{n:1,label:'Forge',key:'forge'},{n:2,label:'OSINT',key:'osint'},{n:3,label:'Inject',key:'inject'},{n:4,label:'Proxy',key:'proxy'},{n:5,label:'Full Patch',key:'patch'},{n:6,label:'Google',key:'google_signin'},{n:7,label:'Trust',key:'trust_score'}]" :key="i">
            <div class="flex items-center gap-1">
              <div class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                :class="provisionJob?.step_n > s.n ? 'bg-green-700 text-green-300' : provisionJob?.step_n === s.n ? 'bg-yellow-700 text-yellow-300 animate-pulse' : 'bg-gray-700 text-gray-500'">
                <span x-text="provisionJob?.step_n > s.n ? '&#10003;' : s.n"></span>
              </div>
              <span class="whitespace-nowrap" :class="provisionJob?.step_n >= s.n ? 'text-white' : 'text-gray-600'" x-text="s.label"></span>
              <span x-show="i < 6" class="text-gray-700 mx-0.5">&#8594;</span>
            </div>
          </template>
        </div>
      </div>

      <!-- Provision scorecard -->
      <div x-show="provisionResult" class="grp border-green-700 bg-green-900/20">
        <div class="text-green-400 font-bold text-sm mb-3">&#9989; Provision Complete</div>
        <div class="grid grid-cols-5 gap-3">
          <div class="text-center">
            <div class="text-2xl font-bold" :class="(provisionResult?.patch_score||0)>=90?'text-green-400':(provisionResult?.patch_score||0)>=70?'text-yellow-400':'text-red-400'" x-text="(provisionResult?.patch_score||0)+'%'"></div>
            <div class="text-[10px] text-gray-500 mt-0.5">Stealth Score</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold" :class="(provisionResult?.trust_score||0)>=90?'text-green-400':(provisionResult?.trust_score||0)>=70?'text-yellow-400':'text-red-400'" x-text="(provisionResult?.trust_score||0)+'/100'"></div>
            <div class="text-[10px] text-gray-500 mt-0.5">Trust Score</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold" :class="provisionResult?.gsm?.ok?'text-green-400':'text-red-400'" x-text="provisionResult?.gsm?.ok ? '&#10003; OK' : '&#10007; FAIL'"></div>
            <div class="text-[10px] text-gray-500 mt-0.5">GSM / SIM</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold" :class="provisionResult?.google_signin?.success?'text-green-400':provisionResult?.google_signin?.skipped?'text-gray-500':'text-red-400'" x-text="provisionResult?.google_signin?.success?'&#10003; OK':provisionResult?.google_signin?.skipped?'&#8212;':'&#10007;'"></div>
            <div class="text-[10px] text-gray-500 mt-0.5">Google Sign-In</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold" :class="provisionResult?.proxy?.skipped?'text-gray-500':provisionResult?.proxy?.error?'text-red-400':'text-green-400'" x-text="provisionResult?.proxy?.skipped?'&#8212;':provisionResult?.proxy?.error?'&#10007;':'&#10003;'"></div>
            <div class="text-[10px] text-gray-500 mt-0.5">Proxy</div>
          </div>
        </div>
        <div class="mt-3 text-xs grid grid-cols-2 gap-x-4 gap-y-1 text-gray-400">
          <template x-for="[k,v] in Object.entries(provisionResult?.trust_checks||{})" :key="k">
            <div class="flex items-center gap-1">
              <span :class="v?'text-green-500':'text-red-500'" x-text="v?'&#10003;':'&#10007;'"></span>
              <span x-text="k.replace(/_/g,' ')"></span>
            </div>
          </template>
        </div>
      </div>

      <!-- OSINT result card -->
      <div x-show="osintResult" class="grp border-purple-700 bg-purple-900/20">
        <div class="flex items-center justify-between mb-2">
          <div class="text-purple-400 font-bold text-sm">&#x1F50D; OSINT Results</div>
          <span class="text-[10px] text-gray-500" x-text="(osintResult?.total_hits||0)+' hits'"></span>
        </div>
        <div class="grid grid-cols-3 gap-3 text-xs">
          <div><span class="text-gray-500">Tools Run:</span> <span class="text-white" x-text="(osintResult?.tools_run||[]).join(', ')||'none'"></span></div>
          <div><span class="text-gray-500">Social Profiles:</span> <span class="text-white" x-text="(osintResult?.social_profiles||[]).length"></span></div>
          <div><span class="text-gray-500">Email Hits:</span> <span class="text-white" x-text="(osintResult?.holehe_hits||[]).length"></span></div>
        </div>
        <div x-show="(osintResult?.tools_missing||[]).length" class="mt-2 text-[10px] text-yellow-500">
          &#9888; Missing tools: <span x-text="(osintResult?.tools_missing||[]).join(', ')"></span> &#8212; install via pip
        </div>
      </div>

      <!-- Forge result -->
      <div x-show="forgeResult && !provisionResult" class="grp border-green-800 bg-green-900/20">
        <div class="text-green-400 font-semibold text-sm mb-2">Profile Forged</div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div><span class="text-gray-500">ID:</span> <span class="text-white font-mono" x-text="forgeResult?.profile_id"></span></div>
          <div><span class="text-gray-500">Name:</span> <span class="text-white" x-text="forgeResult?.persona?.name"></span></div>
          <div><span class="text-gray-500">Email:</span> <span class="text-white" x-text="forgeResult?.persona?.email"></span></div>
          <div><span class="text-gray-500">Phone:</span> <span class="text-white" x-text="forgeResult?.persona?.phone"></span></div>
          <div><span class="text-gray-500">Contacts:</span> <span class="text-white" x-text="forgeResult?.stats?.contacts"></span></div>
          <div><span class="text-gray-500">Calls:</span> <span class="text-white" x-text="forgeResult?.stats?.call_logs"></span></div>
          <div><span class="text-gray-500">Cookies:</span> <span class="text-white" x-text="forgeResult?.stats?.cookies"></span></div>
          <div><span class="text-gray-500">Trust:</span> <span class="text-white font-bold" x-text="forgeResult?.trust_score||'&#8212;'"></span></div>
        </div>
      </div>

      <div class="log-area h-32" x-text="forgeLog||'Configure persona and click FORGE'"></div>
    </div>
  </div>

'''

# Build new file
new_lines = lines[:forge_start] + [NEW_FORGE] + lines[smart_forge_end:]
html_path.write_text("".join(new_lines))
print(f"Done. Old lines {forge_start+1}-{smart_forge_end} replaced. New file has {len(new_lines)} lines.")
