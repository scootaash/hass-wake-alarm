function t(t,e,i,s){var r,o=arguments.length,a=o<3?e:null===s?s=Object.getOwnPropertyDescriptor(e,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)a=Reflect.decorate(t,e,i,s);else for(var n=t.length-1;n>=0;n--)(r=t[n])&&(a=(o<3?r(a):o>3?r(e,i,a):r(e,i))||a);return o>3&&a&&Object.defineProperty(e,i,a),a}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),r=new WeakMap;let o=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&r.set(e,t))}return t}toString(){return this.cssText}};const a=(t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new o(i,t,s)},n=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new o("string"==typeof t?t:t+"",void 0,s))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,m=globalThis,g=m.trustedTypes,_=g?g.emptyScript:"",v=m.reactiveElementPolyfillSupport,f=(t,e)=>t,b={toAttribute(t,e){switch(e){case Boolean:t=t?_:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},y=(t,e)=>!c(t,e),$={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=$){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&l(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:r}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const o=s?.call(this);r?.call(this,e),this.requestUpdate(t,o,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??$}static _$Ei(){if(this.hasOwnProperty(f("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(f("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(f("properties"))){const t=this.properties,e=[...h(t),...p(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(n(t))}else void 0!==t&&e.push(n(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,s)=>{if(i)t.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of s){const s=document.createElement("style"),r=e.litNonce;void 0!==r&&s.setAttribute("nonce",r),s.textContent=i.cssText,t.appendChild(s)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const r=(void 0!==i.converter?.toAttribute?i.converter:b).toAttribute(e,i.type);this._$Em=t,null==r?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:b;this._$Em=s;const o=r.fromAttribute(e,t.type);this[s]=o??this._$Ej?.get(s)??o,this._$Em=null}}requestUpdate(t,e,i,s=!1,r){if(void 0!==t){const o=this.constructor;if(!1===s&&(r=this[t]),i??=o.getPropertyOptions(t),!((i.hasChanged??y)(r,e)||i.useDefault&&i.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:r},o){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),!0!==r||void 0!==o)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[f("elementProperties")]=new Map,w[f("finalized")]=new Map,v?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,k=t=>t,A=x.trustedTypes,E=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,S="$lit$",P=`lit$${Math.random().toFixed(9).slice(2)}$`,C="?"+P,M=`<${C}>`,T=document,z=()=>T.createComment(""),U=t=>null===t||"object"!=typeof t&&"function"!=typeof t,O=Array.isArray,N="[ \t\n\f\r]",R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,H=/-->/g,j=/>/g,D=RegExp(`>|${N}(?:([^\\s"'>=/]+)(${N}*=${N}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),W=/'/g,I=/"/g,L=/^(?:script|style|textarea|title)$/i,B=(t=>(e,...i)=>({_$litType$:t,strings:e,values:i}))(1),q=Symbol.for("lit-noChange"),F=Symbol.for("lit-nothing"),V=new WeakMap,K=T.createTreeWalker(T,129);function J(t,e){if(!O(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(e):e}const Z=(t,e)=>{const i=t.length-1,s=[];let r,o=2===e?"<svg>":3===e?"<math>":"",a=R;for(let e=0;e<i;e++){const i=t[e];let n,c,l=-1,d=0;for(;d<i.length&&(a.lastIndex=d,c=a.exec(i),null!==c);)d=a.lastIndex,a===R?"!--"===c[1]?a=H:void 0!==c[1]?a=j:void 0!==c[2]?(L.test(c[2])&&(r=RegExp("</"+c[2],"g")),a=D):void 0!==c[3]&&(a=D):a===D?">"===c[0]?(a=r??R,l=-1):void 0===c[1]?l=-2:(l=a.lastIndex-c[2].length,n=c[1],a=void 0===c[3]?D:'"'===c[3]?I:W):a===I||a===W?a=D:a===H||a===j?a=R:(a=D,r=void 0);const h=a===D&&t[e+1].startsWith("/>")?" ":"";o+=a===R?i+M:l>=0?(s.push(n),i.slice(0,l)+S+i.slice(l)+P+h):i+P+(-2===l?e:h)}return[J(t,o+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]};class G{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let r=0,o=0;const a=t.length-1,n=this.parts,[c,l]=Z(t,e);if(this.el=G.createElement(c,i),K.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=K.nextNode())&&n.length<a;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(S)){const e=l[o++],i=s.getAttribute(t).split(P),a=/([.?@])?(.*)/.exec(e);n.push({type:1,index:r,name:a[2],strings:i,ctor:"."===a[1]?et:"?"===a[1]?it:"@"===a[1]?st:tt}),s.removeAttribute(t)}else t.startsWith(P)&&(n.push({type:6,index:r}),s.removeAttribute(t));if(L.test(s.tagName)){const t=s.textContent.split(P),e=t.length-1;if(e>0){s.textContent=A?A.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],z()),K.nextNode(),n.push({type:2,index:++r});s.append(t[e],z())}}}else if(8===s.nodeType)if(s.data===C)n.push({type:2,index:r});else{let t=-1;for(;-1!==(t=s.data.indexOf(P,t+1));)n.push({type:7,index:r}),t+=P.length-1}r++}}static createElement(t,e){const i=T.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,s){if(e===q)return e;let r=void 0!==s?i._$Co?.[s]:i._$Cl;const o=U(e)?void 0:e._$litDirective$;return r?.constructor!==o&&(r?._$AO?.(!1),void 0===o?r=void 0:(r=new o(t),r._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=r:i._$Cl=r),void 0!==r&&(e=Q(t,r._$AS(t,e.values),r,s)),e}class X{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??T).importNode(e,!0);K.currentNode=s;let r=K.nextNode(),o=0,a=0,n=i[0];for(;void 0!==n;){if(o===n.index){let e;2===n.type?e=new Y(r,r.nextSibling,this,t):1===n.type?e=new n.ctor(r,n.name,n.strings,this,t):6===n.type&&(e=new rt(r,this,t)),this._$AV.push(e),n=i[++a]}o!==n?.index&&(r=K.nextNode(),o++)}return K.currentNode=T,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class Y{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=F,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),U(t)?t===F||null==t||""===t?(this._$AH!==F&&this._$AR(),this._$AH=F):t!==this._$AH&&t!==q&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>O(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==F&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(T.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=G.createElement(J(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new X(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=V.get(t.strings);return void 0===e&&V.set(t.strings,e=new G(t)),e}k(t){O(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const r of t)s===e.length?e.push(i=new Y(this.O(z()),this.O(z()),this,this.options)):i=e[s],i._$AI(r),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=k(t).nextSibling;k(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class tt{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,r){this.type=1,this._$AH=F,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=r,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=F}_$AI(t,e=this,i,s){const r=this.strings;let o=!1;if(void 0===r)t=Q(this,t,e,0),o=!U(t)||t!==this._$AH&&t!==q,o&&(this._$AH=t);else{const s=t;let a,n;for(t=r[0],a=0;a<r.length-1;a++)n=Q(this,s[i+a],e,a),n===q&&(n=this._$AH[a]),o||=!U(n)||n!==this._$AH[a],n===F?t=F:t!==F&&(t+=(n??"")+r[a+1]),this._$AH[a]=n}o&&!s&&this.j(t)}j(t){t===F?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class et extends tt{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===F?void 0:t}}class it extends tt{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==F)}}class st extends tt{constructor(t,e,i,s,r){super(t,e,i,s,r),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??F)===q)return;const i=this._$AH,s=t===F&&i!==F||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,r=t!==F&&(i===F||s);s&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class rt{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const ot=x.litHtmlPolyfillSupport;ot?.(G,Y),(x.litHtmlVersions??=[]).push("3.3.2");const at=globalThis;class nt extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let r=s._$litPart$;if(void 0===r){const t=i?.renderBefore??null;s._$litPart$=r=new Y(e.insertBefore(z(),t),t,void 0,i??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return q}}nt._$litElement$=!0,nt.finalized=!0,at.litElementHydrateSupport?.({LitElement:nt});const ct=at.litElementPolyfillSupport;ct?.({LitElement:nt}),(at.litElementVersions??=[]).push("4.2.2");const lt=t=>(e,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)},dt={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:y},ht=(t=dt,e,i)=>{const{kind:s,metadata:r}=i;let o=globalThis.litPropertyMetadata.get(r);if(void 0===o&&globalThis.litPropertyMetadata.set(r,o=new Map),"setter"===s&&((t=Object.create(t)).wrapped=!0),o.set(i.name,t),"accessor"===s){const{name:s}=i;return{set(i){const r=e.get.call(this);e.set.call(this,i),this.requestUpdate(s,r,t,!0,i)},init(e){return void 0!==e&&this.C(s,void 0,t,e),e}}}if("setter"===s){const{name:s}=i;return function(i){const r=this[s];e.call(this,i),this.requestUpdate(s,r,t,!0,i)}}throw Error("Unsupported decorator location: "+s)};function pt(t){return(e,i)=>"object"==typeof i?ht(t,e,i):((t,e,i)=>{const s=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),s?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function ut(t){return pt({...t,state:!0,attribute:!1})}const mt=a`
  :host {
    --wa-gap: 16px;
    --wa-radius: 12px;
    --wa-chip-size: 44px;
    --wa-section-gap: 20px;
  }

  ha-card {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: var(--wa-section-gap);
  }

  .header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header .title {
    flex: 1;
    font-size: 1.1rem;
    font-weight: 500;
  }

  .header ha-icon-button {
    --mdc-icon-button-size: 36px;
    color: var(--secondary-text-color);
  }

  .row {
    display: flex;
    align-items: center;
    gap: var(--wa-gap);
  }

  .label {
    flex: 1;
    color: var(--primary-text-color);
    font-size: 0.95rem;
  }

  .value {
    font-variant-numeric: tabular-nums;
    color: var(--secondary-text-color);
  }

  button.btn,
  .btn {
    background: var(--ha-card-background, var(--card-background-color));
    border: 1px solid var(--divider-color);
    color: var(--primary-text-color);
    border-radius: var(--wa-radius);
    padding: 8px 16px;
    font-size: 0.95rem;
    cursor: pointer;
    font-family: inherit;
  }
  button.btn:hover {
    background: var(--secondary-background-color);
  }
  button.btn[disabled] {
    opacity: 0.5;
    cursor: not-allowed;
  }
  button.btn.primary {
    background: var(--primary-color);
    color: var(--text-primary-color);
    border-color: var(--primary-color);
  }
  button.btn.danger {
    background: rgb(255, 82, 82);
    color: white;
    border-color: rgb(255, 82, 82);
  }

  .error {
    color: var(--error-color, rgb(255, 82, 82));
    padding: 16px;
    font-size: 0.95rem;
  }
  .loading {
    padding: 16px;
    color: var(--secondary-text-color);
  }
`,gt=["mon","tue","wed","thu","fri","sat","sun"],_t=["length_min","start_kelvin","target_kelvin","max_brightness_pct","volume","snooze_min","steps_per_min","music_fade_sec","auto_dismiss_min"],vt=["test_light_ramp","cancel_ramp","test_music","dismiss","snooze"],ft=["next_alarm","state","media_selection"];class bt extends Error{}let yt=class extends nt{constructor(){super(...arguments),this._toggleEnabled=()=>{this.hass&&this.related&&this.hass.callService("switch","toggle",{entity_id:this.related.enabled})},this._snooze=()=>{this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons.snooze})},this._dismiss=()=>{this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons.dismiss})},this._goSettings=()=>{this.dispatchEvent(new CustomEvent("navigate-settings",{bubbles:!0,composed:!0}))}}shouldUpdate(t){return t.has("hass")||t.has("related")}render(){if(!this.hass||!this.related)return B``;const t=this.related,e=this.hass.states[t.enabled],i=this.hass.states[t.sensors.state],s=this.hass.states[t.active],r=this.hass.states[t.alarmTime],o=this.hass.states[t.sensors.next_alarm],a="on"===e?.state,n=i?.state??"idle",c="on"===s?.state,l=xt(r?.state),d=$t[n]??$t.idle,h=a?function(t){switch(t){case"ramping":return"Ramping";case"playing":return"Playing";case"snoozing":return"Snoozing";default:return"On"}}(n):"Off",p=o?.state&&"unknown"!==o.state?function(t){const e=new Date(t);if(Number.isNaN(e.getTime()))return t;const i={weekday:"short",hour:"2-digit",minute:"2-digit",hour12:!1};return new Intl.DateTimeFormat(void 0,i).format(e)}(o.state):"No upcoming alarm";return B`
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:alarm"></ha-icon>
          <div class="title">${this._instanceName()}</div>
          <ha-icon-button
            label="Settings"
            @click=${this._goSettings}
          >
            <ha-icon icon="mdi:cog"></ha-icon>
          </ha-icon-button>
        </div>

        <div class="mode-tile mode-${a?n:"off"}" @click=${this._toggleEnabled}>
          <ha-icon icon=${d}></ha-icon>
          <div class="mode-text">
            <div class="mode-label">${h}</div>
            <div class="mode-next">${a?p:"Tap to enable"}</div>
          </div>
        </div>

        <div class="time-picker">
          <div class="time-col">
            <ha-icon-button @click=${()=>this._adjustTime(1,0)}>
              <ha-icon icon="mdi:menu-up"></ha-icon>
            </ha-icon-button>
            <div class="time-num">${kt(l.h)}</div>
            <ha-icon-button @click=${()=>this._adjustTime(-1,0)}>
              <ha-icon icon="mdi:menu-down"></ha-icon>
            </ha-icon-button>
          </div>
          <div class="time-sep">:</div>
          <div class="time-col">
            <ha-icon-button @click=${()=>this._adjustTime(0,1)}>
              <ha-icon icon="mdi:menu-up"></ha-icon>
            </ha-icon-button>
            <div class="time-num">${kt(l.m)}</div>
            <ha-icon-button @click=${()=>this._adjustTime(0,-1)}>
              <ha-icon icon="mdi:menu-down"></ha-icon>
            </ha-icon-button>
          </div>
        </div>

        <div class="day-chips">
          ${gt.map(t=>this._renderDayChip(t))}
        </div>

        ${c?this._renderActiveActions():null}
      </ha-card>
    `}_renderDayChip(t){if(!this.hass||!this.related)return B``;const e=this.related.days[t],i="on"===this.hass.states[e]?.state;return B`
      <div
        class="chip ${i?"chip-on":"chip-off"}"
        @click=${()=>this._toggleDay(t)}
      >
        <ha-icon icon=${i?"mdi:check-circle":"mdi:close-circle-outline"}></ha-icon>
        <span>${wt[t]}</span>
      </div>
    `}_renderActiveActions(){return B`
      <div class="row">
        <button class="btn" @click=${this._snooze}>Snooze</button>
        <button class="btn danger" @click=${this._dismiss}>Dismiss</button>
      </div>
    `}_instanceName(){if(!this.hass||!this.related)return"Wake Alarm";const t=this.hass.states[this.related.enabled]?.attributes?.friendly_name;return t?t.replace(/\s+Enabled$/,""):"Wake Alarm"}_toggleDay(t){this.hass&&this.related&&this.hass.callService("switch","toggle",{entity_id:this.related.days[t]})}_adjustTime(t,e){if(!this.hass||!this.related)return;const i=xt(this.hass.states[this.related.alarmTime]?.state);let s=i.h+t,r=i.m+e;r>=60&&(r-=60,s+=1),r<0&&(r+=60,s-=1),s=(s%24+24)%24,this.hass.callService("time","set_value",{entity_id:this.related.alarmTime,time:`${kt(s)}:${kt(r)}:00`})}};yt.styles=[mt,a`
      .mode-tile {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        border-radius: var(--wa-radius);
        cursor: pointer;
        transition: background 0.15s ease;
      }
      .mode-tile ha-icon {
        --mdc-icon-size: 36px;
      }
      .mode-text { display: flex; flex-direction: column; gap: 2px; }
      .mode-label { font-size: 1rem; font-weight: 500; }
      .mode-next { font-size: 0.85rem; color: var(--secondary-text-color); }

      .mode-off {
        background: var(--ha-card-background, var(--card-background-color));
        border: 1px solid var(--divider-color);
      }
      .mode-off ha-icon { color: var(--disabled-text-color); }
      .mode-idle {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.12);
      }
      .mode-idle ha-icon { color: var(--primary-color); }
      .mode-ramping {
        background: rgba(255, 165, 0, 0.18);
      }
      .mode-ramping ha-icon { color: rgb(255, 165, 0); }
      .mode-playing {
        background: rgba(76, 175, 80, 0.20);
      }
      .mode-playing ha-icon { color: rgb(76, 175, 80); }
      .mode-snoozing {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.20);
      }
      .mode-snoozing ha-icon { color: var(--primary-color); }

      .time-picker {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }
      .time-col {
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      .time-num {
        font-size: 2.2rem;
        font-variant-numeric: tabular-nums;
        font-weight: 500;
        min-width: 64px;
        text-align: center;
      }
      .time-sep {
        font-size: 2.2rem;
        line-height: 2.2rem;
        color: var(--secondary-text-color);
      }

      .day-chips {
        display: flex;
        gap: 8px;
        justify-content: space-between;
      }
      .chip {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 8px 4px;
        border-radius: var(--wa-radius);
        cursor: pointer;
        font-size: 0.8rem;
        background: var(--ha-card-background, var(--card-background-color));
        border: 1px solid var(--divider-color);
        user-select: none;
      }
      .chip-on ha-icon { color: rgb(76, 175, 80); }
      .chip-off ha-icon { color: var(--disabled-text-color); }
      .chip-on { border-color: rgba(76, 175, 80, 0.4); }
    `],t([pt({attribute:!1})],yt.prototype,"hass",void 0),t([pt({attribute:!1})],yt.prototype,"related",void 0),yt=t([lt("wake-alarm-main-view")],yt);const $t={idle:"mdi:alarm",ramping:"mdi:weather-sunset-up",playing:"mdi:music-note",snoozing:"mdi:alarm-snooze",off:"mdi:alarm-off"},wt={mon:"Mon",tue:"Tue",wed:"Wed",thu:"Thu",fri:"Fri",sat:"Sat",sun:"Sun"};function xt(t){if(!t)return{h:7,m:0};const e=/^(\d{1,2}):(\d{1,2})/.exec(t);return e?{h:parseInt(e[1],10),m:parseInt(e[2],10)}:{h:7,m:0}}function kt(t){return t.toString().padStart(2,"0")}const At=[{key:"snooze_min",label:"Snooze (min)",min:1,max:30,step:1},{key:"length_min",label:"Length (min)",min:1,max:120,step:1},{key:"start_kelvin",label:"Start K",min:1500,max:6500,step:50},{key:"target_kelvin",label:"Target K",min:1500,max:6500,step:50},{key:"max_brightness_pct",label:"Max % Brightness",min:1,max:100,step:1},{key:"volume",label:"Alarm Volume (0–1)",min:0,max:1,step:.01},{key:"music_fade_sec",label:"Music fade (s)",min:0,max:300,step:5},{key:"auto_dismiss_min",label:"Auto-dismiss (min)",min:0,max:120,step:1}];let Et=class extends nt{constructor(){super(...arguments),this._showMediaPicker=!1,this._openMediaPicker=()=>{this._showMediaPicker=!0},this._closeMediaPicker=()=>{this._showMediaPicker=!1},this._onMediaPicked=t=>{if(!this.hass||!this.related)return;const e=t.detail?.item;e&&(this.hass.callService("wake_alarm","set_media",{media_content_id:e.media_content_id,media_content_type:e.media_content_type,title:e.title??e.media_content_id,thumbnail:e.thumbnail},{entity_id:this.related.enabled}),this._closeMediaPicker())},this._openOptionsFlow=()=>{this.related&&(history.pushState(null,"","/config/integrations/integration/wake_alarm"),window.dispatchEvent(new Event("location-changed")))},this._goBack=()=>{this.dispatchEvent(new CustomEvent("navigate-back",{bubbles:!0,composed:!0}))}}shouldUpdate(t){return t.has("hass")||t.has("related")||t.has("_showMediaPicker")}render(){if(!this.hass||!this.related)return B``;const t=this.related,e=this.hass.states[t.sensors.state]?.state??"idle",i=this.hass.states[t.sensors.media_selection],s=i?.state??"none",r="none"!==s,o=i?.attributes?.thumbnail,a=this.hass.states[t.sensors.next_alarm],n=a?.attributes?.light_entities??[],c=a?.attributes?.media_player_entities??[],l=a?.attributes?.person_entity;return B`
      <ha-card>
        <div class="header">
          <ha-icon-button label="Back" @click=${this._goBack}>
            <ha-icon icon="mdi:arrow-left"></ha-icon>
          </ha-icon-button>
          <div class="title">Settings</div>
        </div>

        <div class="section">
          ${At.map(t=>this._renderSlider(t))}
        </div>

        <div class="section actions">
          <button class="btn" @click=${()=>this._press("test_light_ramp")}>
            Test light ramp
          </button>
          ${"ramping"===e?B`<button class="btn" @click=${()=>this._press("cancel_ramp")}>
                Cancel ramp
              </button>`:null}
          <button class="btn" @click=${()=>this._press("test_music")}>
            Test music
          </button>
        </div>

        <div class="section media">
          <div class="section-title">Media</div>
          <div class="media-row" @click=${this._openMediaPicker}>
            ${r?B`
                  ${o?B`<img src=${o} alt="" class="thumb" />`:B`<div class="thumb thumb-placeholder">
                        <ha-icon icon="mdi:music"></ha-icon>
                      </div>`}
                  <div class="media-text">
                    <div class="media-title">${s}</div>
                    <div class="media-sub">Tap to change</div>
                  </div>
                `:B`
                  <div class="thumb thumb-placeholder">
                    <ha-icon icon="mdi:music-note-plus"></ha-icon>
                  </div>
                  <div class="media-text">
                    <div class="media-title">No media picked</div>
                    <div class="media-sub">Tap to choose</div>
                  </div>
                `}
          </div>
        </div>

        <div class="section">
          <div class="section-title">Targets</div>
          <div class="targets">
            <div class="target-row">
              <ha-icon icon="mdi:account"></ha-icon>
              <span>${l??"—"}</span>
            </div>
            <div class="target-row">
              <ha-icon icon="mdi:lightbulb"></ha-icon>
              <span>${n.join(", ")||"—"}</span>
            </div>
            <div class="target-row">
              <ha-icon icon="mdi:speaker"></ha-icon>
              <span>${c.join(", ")||"—"}</span>
            </div>
            <button class="btn small" @click=${this._openOptionsFlow}>
              Edit targets in HA settings
            </button>
          </div>
        </div>

        ${this._showMediaPicker?this._renderMediaPickerDialog():null}
      </ha-card>
    `}_renderSlider(t){if(!this.hass||!this.related)return B``;const e=this.related.numbers[t.key],i=this.hass.states[e]?.state,s=i&&!["unknown","unavailable"].includes(i)?Number(i):t.min,r=t.step>=1?s.toFixed(0):s.toFixed(2);return B`
      <div class="slider-row">
        <div class="slider-head">
          <span class="label">${t.label}</span>
          <span class="value">${r}</span>
        </div>
        <input
          type="range"
          min=${t.min}
          max=${t.max}
          step=${t.step}
          .value=${String(s)}
          @change=${t=>this._setNumber(e,t)}
        />
      </div>
    `}_setNumber(t,e){if(!this.hass)return;const i=Number(e.target.value);this.hass.callService("number","set_value",{entity_id:t,value:i})}_press(t){this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons[t]})}_renderMediaPickerDialog(){if(!this.hass||!this.related)return B``;const t=(this.hass.states[this.related.sensors.next_alarm]?.attributes?.media_player_entities??[])[0];return t?B`
      <div class="modal-backdrop" @click=${this._closeMediaPicker}>
        <div class="modal large" @click=${t=>t.stopPropagation()}>
          <div class="modal-header">
            <div class="title">Pick media</div>
            <ha-icon-button @click=${this._closeMediaPicker}>
              <ha-icon icon="mdi:close"></ha-icon>
            </ha-icon-button>
          </div>
          <ha-media-player-browse
            .hass=${this.hass}
            .entityId=${t}
            .navigateIds=${[{media_content_id:void 0,media_content_type:void 0}]}
            @media-picked=${this._onMediaPicked}
          ></ha-media-player-browse>
        </div>
      </div>
    `:B`
        <div class="modal-backdrop" @click=${this._closeMediaPicker}>
          <div class="modal" @click=${t=>t.stopPropagation()}>
            <div class="modal-header">
              <div class="title">Pick media</div>
              <ha-icon-button @click=${this._closeMediaPicker}>
                <ha-icon icon="mdi:close"></ha-icon>
              </ha-icon-button>
            </div>
            <div class="error">
              No media players are configured for this alarm. Add one in
              Settings → Devices & Services.
            </div>
          </div>
        </div>
      `}};Et.styles=[mt,a`
      .section {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .section-title {
        font-size: 0.95rem;
        font-weight: 500;
        color: var(--secondary-text-color);
      }
      .actions {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
      }

      .slider-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .slider-head {
        display: flex;
        align-items: center;
      }
      .slider-row input[type="range"] {
        width: 100%;
        accent-color: var(--primary-color);
      }

      .media-row {
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 8px;
        border-radius: var(--wa-radius);
        background: var(--ha-card-background, var(--card-background-color));
        border: 1px solid var(--divider-color);
        cursor: pointer;
      }
      .media-row:hover { background: var(--secondary-background-color); }
      .thumb {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        object-fit: cover;
      }
      .thumb-placeholder {
        background: var(--secondary-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--secondary-text-color);
      }
      .media-text { display: flex; flex-direction: column; gap: 2px; }
      .media-title { font-size: 1rem; font-weight: 500; }
      .media-sub { font-size: 0.85rem; color: var(--secondary-text-color); }

      .targets {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .target-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9rem;
        color: var(--primary-text-color);
        word-break: break-all;
      }
      .target-row ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color);
      }
      button.btn.small {
        padding: 6px 12px;
        font-size: 0.85rem;
        align-self: flex-start;
      }

      .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999;
      }
      .modal {
        background: var(--card-background-color, white);
        border-radius: var(--wa-radius);
        max-width: 90vw;
        width: 480px;
        max-height: 90vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
      }
      .modal.large {
        width: 720px;
        height: 80vh;
      }
      .modal-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border-bottom: 1px solid var(--divider-color);
      }
      .modal-header .title {
        flex: 1;
        font-size: 1.1rem;
        font-weight: 500;
      }
      ha-media-player-browse {
        flex: 1;
        overflow: auto;
      }
    `],t([pt({attribute:!1})],Et.prototype,"hass",void 0),t([pt({attribute:!1})],Et.prototype,"related",void 0),t([ut()],Et.prototype,"_showMediaPicker",void 0),Et=t([lt("wake-alarm-settings-view")],Et);let St=class extends nt{constructor(){super(...arguments),this._enabledSwitches=[],this._onEntityChange=t=>{const e=t.target.value,i={...this._config??{type:"custom:wake-alarm-card"},entity:e};this._config=i,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:i},bubbles:!0,composed:!0}))}}setConfig(t){this._config=t}firstUpdated(){this._loadEnabledSwitches()}async _loadEnabledSwitches(){if(this.hass)try{const t=await this.hass.callWS({type:"config/entity_registry/list"});this._enabledSwitches=t.filter(t=>"wake_alarm"===t.platform&&(t.unique_id??"").endsWith("_enabled")&&t.entity_id.startsWith("switch.")).map(t=>t.entity_id).sort()}catch(t){this._loadError=`${t}`}}render(){return this._config?this._loadError?B`<div class="error">Failed to load wake_alarm entities: ${this._loadError}</div>`:B`
      <div class="row">
        <label for="entity">Wake Alarm instance</label>
        <select
          id="entity"
          .value=${this._config.entity??""}
          @change=${this._onEntityChange}
        >
          <option value="" disabled ?selected=${!this._config.entity}>
            Pick a wake_alarm enabled-switch…
          </option>
          ${this._enabledSwitches.map(t=>B`<option value=${t} ?selected=${this._config.entity===t}>${t}</option>`)}
        </select>
      </div>
      ${0===this._enabledSwitches.length?B`<div class="hint">
            No wake_alarm instances yet. Add one in
            Settings → Devices &amp; Services → Add Integration → Wake Alarm.
          </div>`:null}
    `:B``}};St.styles=a`
    :host { display: block; padding: 12px; }
    .row { display: flex; flex-direction: column; gap: 6px; }
    label { font-size: 0.9rem; color: var(--secondary-text-color); }
    select {
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--primary-text-color);
      font-size: 0.95rem;
    }
    .hint { padding-top: 8px; color: var(--secondary-text-color); font-size: 0.85rem; }
    .error { color: var(--error-color, rgb(255, 82, 82)); }
  `,t([pt({attribute:!1})],St.prototype,"hass",void 0),t([ut()],St.prototype,"_config",void 0),t([ut()],St.prototype,"_enabledSwitches",void 0),t([ut()],St.prototype,"_loadError",void 0),St=t([lt("wake-alarm-card-editor")],St);let Pt=class extends nt{constructor(){super(...arguments),this._view="main",this._goMain=()=>{this._view="main"},this._goSettings=()=>{this._view="settings"}}setConfig(t){if(!t?.entity)throw new Error("wake-alarm-card: `entity` is required.");if(!t.entity.startsWith("switch."))throw new Error("wake-alarm-card: `entity` must be a switch (the wake_alarm enabled switch).");this._config=t,this._related=void 0,this._resolveError=void 0}getCardSize(){return 6}static getConfigElement(){return document.createElement("wake-alarm-card-editor")}static getStubConfig(){return{type:"custom:wake-alarm-card",entity:""}}willUpdate(t){this.hass&&this._config&&!this._related&&!this._resolveError&&this._resolveRelated()}async _resolveRelated(){if(this.hass&&this._config)try{const t=await this.hass.callWS({type:"config/entity_registry/list"});this._related=function(t,e){const i=e.find(e=>e.entity_id===t);if(!i)throw new bt(`Entity ${t} is not in the entity registry.`);if("wake_alarm"!==i.platform)throw new bt(`Entity ${t} is not a wake_alarm entity (platform=${i.platform}).`);const s=i.config_entry_id;if(!s)throw new bt(`Entity ${t} has no config_entry_id.`);const r={},o=`${s}_`;for(const t of e){if(t.config_entry_id!==s)continue;if(!t.unique_id||!t.unique_id.startsWith(o))continue;const e=t.unique_id.slice(o.length);r[e]=t.entity_id}const a=t=>{const e=r[t];if(!e)throw new bt(`Wake Alarm entity for "${t}" is missing from the registry. Make sure the integration is fully loaded.`);return e},n={};for(const t of gt)n[t]=a(t);const c={};for(const t of _t)c[t]=a(t);const l={};for(const t of vt)l[t]=a(t);const d={};for(const t of ft)d[t]=a(t);return{configEntryId:s,enabled:a("enabled"),active:a("active"),alarmTime:a("alarm_time"),days:n,numbers:c,buttons:l,sensors:d}}(this._config.entity,t)}catch(t){this._resolveError=t instanceof bt?t.message:`Could not resolve wake_alarm entities: ${t}`}}render(){return this._config?this._resolveError?B`<ha-card><div class="error">${this._resolveError}</div></ha-card>`:this._related&&this.hass?"settings"===this._view?B`
          <wake-alarm-settings-view
            .hass=${this.hass}
            .related=${this._related}
            @navigate-back=${this._goMain}
          ></wake-alarm-settings-view>
        `:B`
          <wake-alarm-main-view
            .hass=${this.hass}
            .related=${this._related}
            @navigate-settings=${this._goSettings}
          ></wake-alarm-main-view>
        `:B`<ha-card><div class="loading">Loading…</div></ha-card>`:B``}};Pt.styles=mt,t([pt({attribute:!1})],Pt.prototype,"hass",void 0),t([ut()],Pt.prototype,"_config",void 0),t([ut()],Pt.prototype,"_view",void 0),t([ut()],Pt.prototype,"_related",void 0),t([ut()],Pt.prototype,"_resolveError",void 0),Pt=t([lt("wake-alarm-card")],Pt),window.customCards=window.customCards??[],window.customCards.push({type:"wake-alarm-card",name:"Wake Alarm",description:"Wake-up alarm with a gradual light ramp and a music sequence.",preview:!1}),console.info("%c WAKE-ALARM-CARD %c v0.1.0 ","color: white; background: #ff5722; font-weight: 700;","color: #ff5722; background: white; font-weight: 700;");export{Pt as WakeAlarmCard};
