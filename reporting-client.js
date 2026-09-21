/*
 * PS4 Universal Jailbreak Diagnostics & Stability Reporting
 * Portable browser-side reporting client.
 */
(function (global) {
  "use strict";

  const STORAGE_KEY = "ps4-reporting-active-session-v1";

  function id(prefix) {
    const bytes = new Uint8Array(8);
    if (global.crypto && global.crypto.getRandomValues) global.crypto.getRandomValues(bytes);
    else for (let i=0;i<bytes.length;i++) bytes[i]=Math.floor(Math.random()*256);
    return prefix + "-" + Array.from(bytes, b => ("0"+b.toString(16)).slice(-2)).join("").toUpperCase();
  }

  function now() { return new Date().toISOString(); }

  class PS4ReportingClient {
    constructor(options) {
      options = options || {};
      this.endpoint = options.endpoint || "";
      this.host = options.host || { name:"Unknown Host", version:"unknown", buildId:"unknown" };
      this.firmware = options.firmware || { version:"unknown", source:"unknown" };
      this.payload = options.payload || { name:null, version:null, result:"NOT_ATTEMPTED" };
      this.compatibility = { status: options.compatibility || "UNKNOWN" };
      this.capabilities = options.capabilities || {};
      this.sessionId = id("SESSION");
      this.reportId = id("REPORT");
      this.attempt = options.attempt || 1;
      this.startedAt = now();
      this.lastStage = "SESSION-CREATED";
      this.previousStage = null;
      this.status = "RUNNING";
      this.events = [];
      this.diagnostics = [];
      this.stability = {
        browserCrash:false, browserHang:false, consoleShutdown:false,
        consoleReboot:false, kernelFaultObserved:false, timeout:false
      };
      this.state = {
        userland:"UNKNOWN", readPrimitive:"UNKNOWN",
        writePrimitive:"UNKNOWN", kernel:"NOT_TESTED"
      };
      this.stage("SESSION-CREATED");
    }

    checkpoint() {
      const data = this.buildReport();
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch (_) {}
      return data;
    }

    stage(name, details) {
      const t = Date.now();
      this.previousStage = this.lastStage;
      this.lastStage = String(name);
      this.events.push({ stage:this.lastStage, timestamp:now(), epochMs:t, details:details || null });
      this.checkpoint();
      return this;
    }

    diagnostic(idValue, category, status, details, durationMs) {
      this.diagnostics.push({
        id:String(idValue), category:String(category || "general"),
        status:String(status || "UNKNOWN"),
        durationMs:typeof durationMs === "number" ? durationMs : null,
        details:details || null
      });
      this.checkpoint();
      return this;
    }

    setState(name, value) {
      if (Object.prototype.hasOwnProperty.call(this.state, name)) this.state[name] = String(value);
      this.checkpoint();
      return this;
    }

    setCompatibility(status) {
      var allowed = ["SUPPORTED","EXPERIMENTAL","RESEARCH","UNKNOWN"];
      status = String(status || "UNKNOWN").toUpperCase();
      this.compatibility.status = allowed.indexOf(status) >= 0 ? status : "UNKNOWN";
      this.checkpoint();
      return this;
    }

    setCapability(name, status) {
      this.capabilities[String(name)] = String(status || "UNKNOWN").toUpperCase();
      this.checkpoint();
      return this;
    }

    setPayload(name, version, result) {
      this.payload = { name:name || null, version:version || null, result:result || "NOT_ATTEMPTED" };
      this.checkpoint();
      return this;
    }

    observe(type, value) {
      if (Object.prototype.hasOwnProperty.call(this.stability, type)) this.stability[type] = value !== false;
      this.checkpoint();
      return this;
    }

    failure(stageName, details) {
      if (stageName) this.stage(stageName, details);
      this.status = "FAILURE";
      this.checkpoint();
      return this;
    }

    timeout(stageName) {
      this.stability.timeout = true;
      if (stageName) this.stage(stageName);
      this.status = "TIMEOUT";
      this.checkpoint();
      return this;
    }

    success() {
      this.status = "SUCCESS";
      this.stage("JAILBREAK-COMPLETE");
      this.checkpoint();
      return this;
    }

    buildReport() {
      return {
        schema:"ps4-community-report-1",
        reportId:this.reportId, sessionId:this.sessionId,
        timestamp:now(), startedAt:this.startedAt, platform:"PS4",
        firmware:this.firmware, host:this.host,
        test:{ attempt:this.attempt, status:this.status, lastStage:this.lastStage, previousStage:this.previousStage },
        state:this.state, compatibility:this.compatibility, capabilities:this.capabilities, payload:this.payload, stability:this.stability,
        events:this.events, diagnostics:this.diagnostics
      };
    }

    async submit() {
      if (!this.endpoint) throw new Error("No reporting endpoint configured");
      const response = await fetch(this.endpoint, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify(this.buildReport())
      });
      if (!response.ok) throw new Error("Report submission failed: HTTP " + response.status);
      const result = await response.json();
      if (this.status !== "RUNNING") try { localStorage.removeItem(STORAGE_KEY); } catch (_) {}
      return result;
    }

    static recoverInterrupted() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const report = JSON.parse(raw);
        if (report && report.test && report.test.status === "RUNNING") {
          report.test.status = "INTERRUPTED";
          report.recoveredAt = now();
          return report;
        }
      } catch (_) {}
      return null;
    }

    static discardInterrupted() {
      try { localStorage.removeItem(STORAGE_KEY); } catch (_) {}
    }
  }

  global.PS4ReportingClient = PS4ReportingClient;
})(typeof window !== "undefined" ? window : this);
