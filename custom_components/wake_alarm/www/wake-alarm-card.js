function t(t,e,i,s){var o,a=arguments.length,r=a<3?e:null===s?s=Object.getOwnPropertyDescriptor(e,i):s;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)r=Reflect.decorate(t,e,i,s);else for(var n=t.length-1;n>=0;n--)(o=t[n])&&(r=(a<3?o(r):a>3?o(e,i,r):o(e,i))||r);return a>3&&r&&Object.defineProperty(e,i,r),r}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,i=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s=Symbol(),o=new WeakMap;let a=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==s)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(i&&void 0===t){const i=void 0!==e&&1===e.length;i&&(t=o.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&o.set(e,t))}return t}toString(){return this.cssText}};const r=(t,...e)=>{const i=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new a(i,t,s)},n=i?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new a("string"==typeof t?t:t+"",void 0,s))(e)})(t):t,{is:c,defineProperty:l,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:p,getPrototypeOf:u}=Object,m=globalThis,g=m.trustedTypes,_=g?g.emptyScript:"",v=m.reactiveElementPolyfillSupport,f=(t,e)=>t,b={toAttribute(t,e){switch(e){case Boolean:t=t?_:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},y=(t,e)=>!c(t,e),$={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),m.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=$){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&l(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:o}=d(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const a=s?.call(this);o?.call(this,e),this.requestUpdate(t,a,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??$}static _$Ei(){if(this.hasOwnProperty(f("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(f("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(f("properties"))){const t=this.properties,e=[...h(t),...p(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(n(t))}else void 0!==t&&e.push(n(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,s)=>{if(i)t.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const i of s){const s=document.createElement("style"),o=e.litNonce;void 0!==o&&s.setAttribute("nonce",o),s.textContent=i.cssText,t.appendChild(s)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const o=(void 0!==i.converter?.toAttribute?i.converter:b).toAttribute(e,i.type);this._$Em=t,null==o?this.removeAttribute(s):this.setAttribute(s,o),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),o="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:b;this._$Em=s;const a=o.fromAttribute(e,t.type);this[s]=a??this._$Ej?.get(s)??a,this._$Em=null}}requestUpdate(t,e,i,s=!1,o){if(void 0!==t){const a=this.constructor;if(!1===s&&(o=this[t]),i??=a.getPropertyOptions(t),!((i.hasChanged??y)(o,e)||i.useDefault&&i.reflect&&o===this._$Ej?.get(t)&&!this.hasAttribute(a._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:o},a){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,a??e??this[t]),!0!==o||void 0!==a)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[f("elementProperties")]=new Map,w[f("finalized")]=new Map,v?.({ReactiveElement:w}),(m.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,k=t=>t,A=x.trustedTypes,E=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,S="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+C,M=`<${P}>`,T=document,z=()=>T.createComment(""),U=t=>null===t||"object"!=typeof t&&"function"!=typeof t,N=Array.isArray,O="[ \t\n\f\r]",R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,H=/-->/g,j=/>/g,I=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),D=/'/g,W=/"/g,L=/^(?:script|style|textarea|title)$/i,B=(t=>(e,...i)=>({_$litType$:t,strings:e,values:i}))(1),q=Symbol.for("lit-noChange"),F=Symbol.for("lit-nothing"),V=new WeakMap,K=T.createTreeWalker(T,129);function J(t,e){if(!N(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(e):e}const Z=(t,e)=>{const i=t.length-1,s=[];let o,a=2===e?"<svg>":3===e?"<math>":"",r=R;for(let e=0;e<i;e++){const i=t[e];let n,c,l=-1,d=0;for(;d<i.length&&(r.lastIndex=d,c=r.exec(i),null!==c);)d=r.lastIndex,r===R?"!--"===c[1]?r=H:void 0!==c[1]?r=j:void 0!==c[2]?(L.test(c[2])&&(o=RegExp("</"+c[2],"g")),r=I):void 0!==c[3]&&(r=I):r===I?">"===c[0]?(r=o??R,l=-1):void 0===c[1]?l=-2:(l=r.lastIndex-c[2].length,n=c[1],r=void 0===c[3]?I:'"'===c[3]?W:D):r===W||r===D?r=I:r===H||r===j?r=R:(r=I,o=void 0);const h=r===I&&t[e+1].startsWith("/>")?" ":"";a+=r===R?i+M:l>=0?(s.push(n),i.slice(0,l)+S+i.slice(l)+C+h):i+C+(-2===l?e:h)}return[J(t,a+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]};class G{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let o=0,a=0;const r=t.length-1,n=this.parts,[c,l]=Z(t,e);if(this.el=G.createElement(c,i),K.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=K.nextNode())&&n.length<r;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(S)){const e=l[a++],i=s.getAttribute(t).split(C),r=/([.?@])?(.*)/.exec(e);n.push({type:1,index:o,name:r[2],strings:i,ctor:"."===r[1]?et:"?"===r[1]?it:"@"===r[1]?st:tt}),s.removeAttribute(t)}else t.startsWith(C)&&(n.push({type:6,index:o}),s.removeAttribute(t));if(L.test(s.tagName)){const t=s.textContent.split(C),e=t.length-1;if(e>0){s.textContent=A?A.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],z()),K.nextNode(),n.push({type:2,index:++o});s.append(t[e],z())}}}else if(8===s.nodeType)if(s.data===P)n.push({type:2,index:o});else{let t=-1;for(;-1!==(t=s.data.indexOf(C,t+1));)n.push({type:7,index:o}),t+=C.length-1}o++}}static createElement(t,e){const i=T.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,s){if(e===q)return e;let o=void 0!==s?i._$Co?.[s]:i._$Cl;const a=U(e)?void 0:e._$litDirective$;return o?.constructor!==a&&(o?._$AO?.(!1),void 0===a?o=void 0:(o=new a(t),o._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=o:i._$Cl=o),void 0!==o&&(e=Q(t,o._$AS(t,e.values),o,s)),e}class X{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??T).importNode(e,!0);K.currentNode=s;let o=K.nextNode(),a=0,r=0,n=i[0];for(;void 0!==n;){if(a===n.index){let e;2===n.type?e=new Y(o,o.nextSibling,this,t):1===n.type?e=new n.ctor(o,n.name,n.strings,this,t):6===n.type&&(e=new ot(o,this,t)),this._$AV.push(e),n=i[++r]}a!==n?.index&&(o=K.nextNode(),a++)}return K.currentNode=T,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class Y{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=F,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),U(t)?t===F||null==t||""===t?(this._$AH!==F&&this._$AR(),this._$AH=F):t!==this._$AH&&t!==q&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>N(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==F&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(T.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=G.createElement(J(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new X(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=V.get(t.strings);return void 0===e&&V.set(t.strings,e=new G(t)),e}k(t){N(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const o of t)s===e.length?e.push(i=new Y(this.O(z()),this.O(z()),this,this.options)):i=e[s],i._$AI(o),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=k(t).nextSibling;k(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class tt{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,o){this.type=1,this._$AH=F,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=o,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=F}_$AI(t,e=this,i,s){const o=this.strings;let a=!1;if(void 0===o)t=Q(this,t,e,0),a=!U(t)||t!==this._$AH&&t!==q,a&&(this._$AH=t);else{const s=t;let r,n;for(t=o[0],r=0;r<o.length-1;r++)n=Q(this,s[i+r],e,r),n===q&&(n=this._$AH[r]),a||=!U(n)||n!==this._$AH[r],n===F?t=F:t!==F&&(t+=(n??"")+o[r+1]),this._$AH[r]=n}a&&!s&&this.j(t)}j(t){t===F?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class et extends tt{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===F?void 0:t}}class it extends tt{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==F)}}class st extends tt{constructor(t,e,i,s,o){super(t,e,i,s,o),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??F)===q)return;const i=this._$AH,s=t===F&&i!==F||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,o=t!==F&&(i===F||s);s&&this.element.removeEventListener(this.name,this,i),o&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class ot{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const at=x.litHtmlPolyfillSupport;at?.(G,Y),(x.litHtmlVersions??=[]).push("3.3.2");const rt=globalThis;class nt extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let o=s._$litPart$;if(void 0===o){const t=i?.renderBefore??null;s._$litPart$=o=new Y(e.insertBefore(z(),t),t,void 0,i??{})}return o._$AI(t),o})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return q}}nt._$litElement$=!0,nt.finalized=!0,rt.litElementHydrateSupport?.({LitElement:nt});const ct=rt.litElementPolyfillSupport;ct?.({LitElement:nt}),(rt.litElementVersions??=[]).push("4.2.2");const lt=t=>(e,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)},dt={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:y},ht=(t=dt,e,i)=>{const{kind:s,metadata:o}=i;let a=globalThis.litPropertyMetadata.get(o);if(void 0===a&&globalThis.litPropertyMetadata.set(o,a=new Map),"setter"===s&&((t=Object.create(t)).wrapped=!0),a.set(i.name,t),"accessor"===s){const{name:s}=i;return{set(i){const o=e.get.call(this);e.set.call(this,i),this.requestUpdate(s,o,t,!0,i)},init(e){return void 0!==e&&this.C(s,void 0,t,e),e}}}if("setter"===s){const{name:s}=i;return function(i){const o=this[s];e.call(this,i),this.requestUpdate(s,o,t,!0,i)}}throw Error("Unsupported decorator location: "+s)};function pt(t){return(e,i)=>"object"==typeof i?ht(t,e,i):((t,e,i)=>{const s=e.hasOwnProperty(i);return e.constructor.createProperty(i,t),s?Object.getOwnPropertyDescriptor(e,i):void 0})(t,e,i)}function ut(t){return pt({...t,state:!0,attribute:!1})}const mt=r`
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
`,gt=["mon","tue","wed","thu","fri","sat","sun"],_t={d1_mon:"mon",d2_tue:"tue",d3_wed:"wed",d4_thu:"thu",d5_fri:"fri",d6_sat:"sat",d7_sun:"sun"},vt=["length_min","start_kelvin","target_kelvin","max_brightness_pct","volume","snooze_min","steps_per_min","music_fade_sec","auto_dismiss_min"],ft=["test_light_ramp","cancel_ramp","test_music","test_standard_notification","test_urgent_notification","dismiss","snooze"],bt=["next_alarm","state","media_selection"];class yt extends Error{}let $t=class extends nt{constructor(){super(...arguments),this._cancelRamp=()=>{this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons.cancel_ramp})},this._toggleEnabled=()=>{this.hass&&this.related&&this.hass.callService("switch","toggle",{entity_id:this.related.enabled})},this._handleModeTileClick=()=>{if(!this.hass||!this.related)return;const t=this.hass.states[this.related.sensors.state]?.state;t&&"idle"!==t||this._toggleEnabled()},this._snooze=()=>{this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons.snooze})},this._dismiss=()=>{this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons.dismiss})},this._goSettings=()=>{this.dispatchEvent(new CustomEvent("navigate-settings",{bubbles:!0,composed:!0}))}}disconnectedCallback(){super.disconnectedCallback(),this._stopTicker()}updated(){"snoozing"===(this.hass&&this.related?this.hass.states[this.related.sensors.state]?.state:void 0)?this._startTicker():this._stopTicker()}_startTicker(){void 0===this._tickInterval&&(this._tickInterval=window.setInterval(()=>this.requestUpdate(),1e3))}_stopTicker(){void 0!==this._tickInterval&&(window.clearInterval(this._tickInterval),this._tickInterval=void 0)}render(){if(!this.hass||!this.related)return B``;const t=this.related,e=this.hass.states[t.enabled],i=this.hass.states[t.sensors.state],s=this.hass.states[t.active],o=this.hass.states[t.alarmTime],a=this.hass.states[t.sensors.next_alarm],r="on"===e?.state,n=i?.state??"idle",c="on"===s?.state,l=kt(o?.state),d=wt[n]??wt.idle,h=r?function(t){switch(t){case"ramping":return"Ramping";case"playing":return"Playing";case"snoozing":return"Snoozing";default:return"On"}}(n):"Off",p=i?.attributes?.snooze_until,u="snoozing"===n&&p?function(t){const e=new Date(t).getTime();if(Number.isNaN(e))return t;const i=Math.max(0,Math.round((e-Date.now())/1e3)),s=Math.floor(i/60);return`${s}:${At(i%60)}`}(p):null,m=u?`Music in ${u}`:a?.state&&"unknown"!==a.state?function(t){const e=new Date(t);if(Number.isNaN(e.getTime()))return t;const i={weekday:"short",hour:"2-digit",minute:"2-digit",hour12:!1};return new Intl.DateTimeFormat(void 0,i).format(e)}(a.state):"No upcoming alarm";return B`
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

        <div class="mode-tile mode-${r?n:"off"}" @click=${this._handleModeTileClick}>
          <ha-icon icon=${d}></ha-icon>
          <div class="mode-text">
            <div class="mode-label">${h}</div>
            <div class="mode-next">${r?m:"Tap to enable"}</div>
          </div>
        </div>

        <div class="time-picker">
          <div class="time-col">
            <ha-icon-button @click=${()=>this._adjustTime(1,0)}>
              <ha-icon icon="mdi:menu-up"></ha-icon>
            </ha-icon-button>
            <div class="time-num">${At(l.h)}</div>
            <ha-icon-button @click=${()=>this._adjustTime(-1,0)}>
              <ha-icon icon="mdi:menu-down"></ha-icon>
            </ha-icon-button>
          </div>
          <div class="time-sep">:</div>
          <div class="time-col">
            <ha-icon-button @click=${()=>this._adjustTime(0,1)}>
              <ha-icon icon="mdi:menu-up"></ha-icon>
            </ha-icon-button>
            <div class="time-num">${At(l.m)}</div>
            <ha-icon-button @click=${()=>this._adjustTime(0,-1)}>
              <ha-icon icon="mdi:menu-down"></ha-icon>
            </ha-icon-button>
          </div>
        </div>

        <div class="day-chips">
          ${gt.map(t=>this._renderDayChip(t))}
        </div>

        ${c?this._renderActiveActions(n):null}
      </ha-card>
    `}_renderDayChip(t){if(!this.hass||!this.related)return B``;const e=this.related.days[t],i="on"===this.hass.states[e]?.state;return B`
      <div
        class="chip ${i?"chip-on":"chip-off"}"
        @click=${()=>this._toggleDay(t)}
      >
        <ha-icon icon=${i?"mdi:check-circle":"mdi:close-circle-outline"}></ha-icon>
        <span>${xt[t]}</span>
      </div>
    `}_renderActiveActions(t){return B`
      <div class="action-row">
        ${"ramping"===t?B`
              <button class="action-btn cancel-ramp" @click=${this._cancelRamp}>
                <ha-icon icon="mdi:weather-sunset-down"></ha-icon>
                <span>Cancel ramp</span>
              </button>
            `:null}
        <button class="action-btn snooze" @click=${this._snooze}>
          <ha-icon icon="mdi:alarm-snooze"></ha-icon>
          <span>Snooze</span>
        </button>
        <button class="action-btn dismiss" @click=${this._dismiss}>
          <ha-icon icon="mdi:alarm-off"></ha-icon>
          <span>Dismiss</span>
        </button>
      </div>
    `}_instanceName(){if(!this.hass||!this.related)return"Wake Alarm";const t=this.hass.states[this.related.sensors.next_alarm],e=t?.attributes?.instance_name;return e&&e.trim()?e:"Wake Alarm"}_toggleDay(t){this.hass&&this.related&&this.hass.callService("switch","toggle",{entity_id:this.related.days[t]})}_adjustTime(t,e){if(!this.hass||!this.related)return;const i=kt(this.hass.states[this.related.alarmTime]?.state);let s=i.h+t,o=i.m+e;o>=60&&(o-=60,s+=1),o<0&&(o+=60,s-=1),s=(s%24+24)%24,this.hass.callService("time","set_value",{entity_id:this.related.alarmTime,time:`${At(s)}:${At(o)}:00`})}};$t.styles=[mt,r`
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

      /* Snooze + Dismiss share the mode-tile vibe: tall, prominent,
         half-width each so they line up under the mode tile. */
      .action-row {
        display: flex;
        gap: 12px;
      }
      .action-btn {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 16px;
        border-radius: var(--wa-radius);
        border: 1px solid var(--divider-color);
        background: var(--ha-card-background, var(--card-background-color));
        color: var(--primary-text-color);
        font-size: 1rem;
        font-weight: 500;
        font-family: inherit;
        cursor: pointer;
        transition: background 0.15s ease;
      }
      .action-btn:hover { background: var(--secondary-background-color); }
      .action-btn ha-icon { --mdc-icon-size: 32px; }
      .action-btn.snooze {
        background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.14);
      }
      .action-btn.snooze ha-icon { color: var(--primary-color); }
      .action-btn.dismiss {
        background: rgba(255, 82, 82, 0.14);
        color: rgb(255, 82, 82);
      }
      .action-btn.dismiss ha-icon { color: rgb(255, 82, 82); }
      .action-btn.cancel-ramp {
        background: rgba(255, 165, 0, 0.16);
      }
      .action-btn.cancel-ramp ha-icon { color: rgb(255, 165, 0); }
    `],t([pt({attribute:!1})],$t.prototype,"hass",void 0),t([pt({attribute:!1})],$t.prototype,"related",void 0),$t=t([lt("wake-alarm-main-view")],$t);const wt={idle:"mdi:alarm",ramping:"mdi:weather-sunset-up",playing:"mdi:music-note",snoozing:"mdi:alarm-snooze",off:"mdi:alarm-off"},xt={mon:"Mon",tue:"Tue",wed:"Wed",thu:"Thu",fri:"Fri",sat:"Sat",sun:"Sun"};function kt(t){if(!t)return{h:7,m:0};const e=/^(\d{1,2}):(\d{1,2})/.exec(t);return e?{h:parseInt(e[1],10),m:parseInt(e[2],10)}:{h:7,m:0}}function At(t){return t.toString().padStart(2,"0")}let Et=class extends nt{constructor(){super(...arguments),this._children=[],this._path=[],this._loading=!1}firstUpdated(){this._navigate(void 0,void 0,"Library")}async _navigate(t,e,i){if(this.hass&&this.entityId){this._loading=!0,this._error=void 0;try{const s={type:"media_player/browse_media",entity_id:this.entityId,...void 0!==t?{media_content_id:t}:{},...void 0!==e?{media_content_type:e}:{}},o=await this.hass.callWS(s);this._children=o.children??[],this._path=[...this._path,{contentId:t,contentType:e,title:o.title||i}]}catch(t){this._error=`${t}`}finally{this._loading=!1}}}async _back(){if(this._path.length<=1)return;const t=this._path.slice(0,-1),e=t[t.length-1];this._path=t.slice(0,-1),await this._navigate(e.contentId,e.contentType,e.title)}_onItemClick(t){if(t.can_expand)this._navigate(t.media_content_id,t.media_content_type,t.title);else if(t.can_play){const e={media_content_id:t.media_content_id,media_content_type:t.media_content_type,title:t.title,thumbnail:t.thumbnail??void 0};this.dispatchEvent(new CustomEvent("media-picked",{detail:{item:e},bubbles:!0,composed:!0}))}}render(){const t=this._path.map(t=>t.title).join(" › ")||"Library";return B`
      <div class="toolbar">
        <button
          class="back"
          ?disabled=${this._path.length<=1}
          @click=${this._back}
        >
          <ha-icon icon="mdi:arrow-left"></ha-icon>
        </button>
        <div class="crumb" title=${t}>${t}</div>
      </div>

      ${this._error?B`<div class="error">Failed to browse: ${this._error}</div>`:null}
      ${this._loading?B`<div class="loading">Loading…</div>`:B`
            <div class="grid">
              ${0===this._children.length?B`<div class="empty">Nothing to show.</div>`:this._children.map(t=>this._renderItem(t))}
            </div>
          `}
    `}_renderItem(t){const e=!!t.can_play,i=!!t.can_expand;return B`
      <div class=${`tile ${e?"playable":""} ${i?"expandable":""}`} @click=${()=>this._onItemClick(t)} role="button" tabindex="0">
        ${t.thumbnail?B`<img src=${t.thumbnail} alt="" />`:B`<div class="placeholder">
              <ha-icon icon=${i?"mdi:folder-music":"mdi:music"}></ha-icon>
            </div>`}
        <div class="title" title=${t.title}>${t.title}</div>
      </div>
    `}};Et.styles=r`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      min-height: 0;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-bottom: 1px solid var(--divider-color);
    }
    .toolbar .back {
      background: none;
      border: none;
      cursor: pointer;
      color: inherit;
      padding: 4px;
    }
    .toolbar .back[disabled] {
      opacity: 0.4;
      cursor: not-allowed;
    }
    .crumb {
      flex: 1;
      font-size: 0.95rem;
      color: var(--secondary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 12px;
      padding: 12px;
      overflow-y: auto;
      flex: 1;
    }
    .tile {
      display: flex;
      flex-direction: column;
      gap: 6px;
      cursor: pointer;
      border-radius: 8px;
      overflow: hidden;
      background: var(--secondary-background-color);
      padding: 8px;
      user-select: none;
    }
    .tile:hover { background: var(--ha-card-background, var(--card-background-color)); }
    .tile img,
    .tile .placeholder {
      width: 100%;
      aspect-ratio: 1 / 1;
      object-fit: cover;
      border-radius: 6px;
      background: var(--card-background-color);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--secondary-text-color);
    }
    .tile .title {
      font-size: 0.85rem;
      line-height: 1.2;
      max-height: 2.4em;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
    .tile.playable { outline: 1px solid rgba(76, 175, 80, 0.3); }
    .empty,
    .loading,
    .error {
      padding: 16px;
      color: var(--secondary-text-color);
    }
    .error { color: var(--error-color, rgb(255, 82, 82)); }
  `,t([pt({attribute:!1})],Et.prototype,"hass",void 0),t([pt()],Et.prototype,"entityId",void 0),t([ut()],Et.prototype,"_children",void 0),t([ut()],Et.prototype,"_path",void 0),t([ut()],Et.prototype,"_loading",void 0),t([ut()],Et.prototype,"_error",void 0),Et=t([lt("wake-alarm-media-browser")],Et);const St=[{key:"snooze_min",label:"Snooze (min)",description:"How long the snooze pause lasts before music resumes.",min:1,max:30,step:1},{key:"length_min",label:"Length (min)",description:"Total minutes the lights ramp up before the alarm time.",min:1,max:120,step:1},{key:"start_kelvin",label:"Start K",description:"Warm colour temperature at the beginning of the ramp.",min:1500,max:6500,step:50},{key:"target_kelvin",label:"Target K",description:"Cool colour temperature reached at the alarm time.",min:1500,max:6500,step:50},{key:"max_brightness_pct",label:"Max % Brightness",description:"Peak brightness reached at the alarm time.",min:1,max:100,step:1},{key:"volume",label:"Alarm Volume (%)",description:"Final volume the music fades up to. Defaults to a low value so test plays don't blast.",min:0,max:100,step:1,displayMultiplier:100},{key:"music_fade_sec",label:"Music fade (s)",description:"How long the volume takes to fade from 0 to the target volume.",min:0,max:300,step:5},{key:"auto_dismiss_min",label:"Auto-dismiss (min)",description:"Stop everything automatically after this long. 0 disables.",min:0,max:120,step:1}];let Ct=class extends nt{constructor(){super(...arguments),this._showMediaPicker=!1,this._openMediaPicker=()=>{this._showMediaPicker=!0},this._closeMediaPicker=()=>{this._showMediaPicker=!1},this._onMediaPicked=t=>{if(!this.hass||!this.related)return;const e=t.detail?.item;e&&(this.hass.callService("wake_alarm","set_media",{media_content_id:e.media_content_id,media_content_type:e.media_content_type,title:e.title??e.media_content_id,thumbnail:e.thumbnail},{entity_id:this.related.enabled}),this._closeMediaPicker())},this._openOptionsFlow=()=>{this.related&&(history.pushState(null,"","/config/integrations/integration/wake_alarm"),window.dispatchEvent(new Event("location-changed")))},this._goBack=()=>{this.dispatchEvent(new CustomEvent("navigate-back",{bubbles:!0,composed:!0}))}}shouldUpdate(t){return t.has("hass")||t.has("related")||t.has("_showMediaPicker")}render(){if(!this.hass||!this.related)return B``;const t=this.related,e=this.hass.states[t.sensors.state]?.state??"idle",i=this.hass.states[t.sensors.media_selection],s=i?.state??"none",o="none"!==s,a=i?.attributes?.thumbnail,r=this.hass.states[t.sensors.next_alarm],n=r?.attributes?.light_entities??[],c=r?.attributes?.media_player_entities??[],l=r?.attributes?.person_entity;return B`
      <ha-card>
        <div class="header">
          <ha-icon-button label="Back" @click=${this._goBack}>
            <ha-icon icon="mdi:arrow-left"></ha-icon>
          </ha-icon-button>
          <div class="title">Settings</div>
        </div>

        <div class="section">
          ${St.map(t=>this._renderSlider(t))}
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
          <button
            class="btn"
            @click=${()=>this._press("test_standard_notification")}
            title="Send the standard alarm notification now"
          >
            Test standard notification
          </button>
          <button
            class="btn"
            @click=${()=>this._press("test_urgent_notification")}
            title="Send the urgent (critical) notification now"
          >
            Test urgent notification
          </button>
        </div>

        <div class="section media">
          <div class="section-title">Media</div>
          <div class="media-row" @click=${this._openMediaPicker}>
            ${o?B`
                  ${a?B`<img src=${a} alt="" class="thumb" />`:B`<div class="thumb thumb-placeholder">
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
    `}_renderSlider(t){if(!this.hass||!this.related)return B``;const e=this.related.numbers[t.key],i=this.hass.states[e]?.state,s=i&&!["unknown","unavailable"].includes(i)?Number(i):t.min/(t.displayMultiplier??1),o=t.displayMultiplier??1,a=s*o,r=t.step>=1?a.toFixed(0):a.toFixed(2);return B`
      <div class="slider-row">
        <div class="slider-head">
          <span class="label">${t.label}</span>
          <span class="value">${r}</span>
        </div>
        <div class="slider-desc">${t.description}</div>
        <input
          type="range"
          min=${t.min}
          max=${t.max}
          step=${t.step}
          .value=${String(a)}
          @change=${t=>this._setNumber(e,t,o)}
        />
      </div>
    `}_setNumber(t,e,i){if(!this.hass)return;const s=Number(e.target.value)/i;this.hass.callService("number","set_value",{entity_id:t,value:s})}_press(t){this.hass&&this.related&&this.hass.callService("button","press",{entity_id:this.related.buttons[t]})}_renderMediaPickerDialog(){if(!this.hass||!this.related)return B``;const t=(this.hass.states[this.related.sensors.next_alarm]?.attributes?.media_player_entities??[])[0];return t?B`
      <div class="modal-backdrop" @click=${this._closeMediaPicker}>
        <div class="modal large" @click=${t=>t.stopPropagation()}>
          <div class="modal-header">
            <div class="title">Pick media</div>
            <ha-icon-button @click=${this._closeMediaPicker}>
              <ha-icon icon="mdi:close"></ha-icon>
            </ha-icon-button>
          </div>
          <wake-alarm-media-browser
            .hass=${this.hass}
            .entityId=${t}
            @media-picked=${this._onMediaPicked}
          ></wake-alarm-media-browser>
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
      `}};Ct.styles=[mt,r`
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
      .slider-desc {
        font-size: 0.8rem;
        color: var(--secondary-text-color);
        line-height: 1.3;
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
      wake-alarm-media-browser {
        flex: 1;
        overflow: auto;
        min-height: 0;
      }
    `],t([pt({attribute:!1})],Ct.prototype,"hass",void 0),t([pt({attribute:!1})],Ct.prototype,"related",void 0),t([ut()],Ct.prototype,"_showMediaPicker",void 0),Ct=t([lt("wake-alarm-settings-view")],Ct);let Pt=class extends nt{constructor(){super(...arguments),this._enabledSwitches=[],this._onEntityChange=t=>{const e=t.target.value,i={...this._config??{type:"custom:wake-alarm-card"},entity:e};this._config=i,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:i},bubbles:!0,composed:!0}))}}setConfig(t){this._config=t}firstUpdated(){this._loadEnabledSwitches()}async _loadEnabledSwitches(){if(this.hass)try{const t=await this.hass.callWS({type:"config/entity_registry/list"});if(this._enabledSwitches=t.filter(t=>"wake_alarm"===t.platform&&(t.unique_id??"").endsWith("_enabled")&&t.entity_id.startsWith("switch.")).map(t=>t.entity_id).sort(),this._config?.entity&&!this._enabledSwitches.includes(this._config.entity)){const t={...this._config,entity:""};this._config=t,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:t},bubbles:!0,composed:!0}))}}catch(t){this._loadError=`${t}`}}render(){return this._config?this._loadError?B`<div class="error">Failed to load wake_alarm entities: ${this._loadError}</div>`:B`
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
    `:B``}};Pt.styles=r`
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
  `,t([pt({attribute:!1})],Pt.prototype,"hass",void 0),t([ut()],Pt.prototype,"_config",void 0),t([ut()],Pt.prototype,"_enabledSwitches",void 0),t([ut()],Pt.prototype,"_loadError",void 0),Pt=t([lt("wake-alarm-card-editor")],Pt);let Mt=class extends nt{constructor(){super(...arguments),this._view="main",this._goMain=()=>{this._view="main"},this._goSettings=()=>{this._view="settings"}}setConfig(t){if(t?.entity&&!t.entity.startsWith("switch."))throw new Error("wake-alarm-card: `entity` must be a switch (the wake_alarm enabled switch).");this._config=t??{type:"custom:wake-alarm-card",entity:""},this._related=void 0,this._resolveError=void 0}getCardSize(){return 6}static getConfigElement(){return document.createElement("wake-alarm-card-editor")}static async getStubConfig(t){if(!t)return{type:"custom:wake-alarm-card",entity:""};try{const e=(await t.callWS({type:"config/entity_registry/list"})).find(t=>"wake_alarm"===t.platform&&(t.unique_id??"").endsWith("_enabled")&&(t.entity_id??"").startsWith("switch."));return{type:"custom:wake-alarm-card",entity:e?.entity_id??""}}catch{return{type:"custom:wake-alarm-card",entity:""}}}willUpdate(t){this.hass&&this._config?.entity&&!this._related&&!this._resolveError&&this._resolveRelated()}async _resolveRelated(){if(this.hass&&this._config)try{const t=await this.hass.callWS({type:"config/entity_registry/list"});this._related=function(t,e){const i=e.find(e=>e.entity_id===t);if(!i)throw new yt(`Entity ${t} is not in the entity registry.`);if("wake_alarm"!==i.platform)throw new yt(`Entity ${t} is not a wake_alarm entity (platform=${i.platform}).`);const s=i.config_entry_id;if(!s)throw new yt(`Entity ${t} has no config_entry_id.`);const o={},a={},r=`${s}_`;for(const t of e){if(t.config_entry_id!==s)continue;if(!t.unique_id||!t.unique_id.startsWith(r))continue;const e=t.unique_id.slice(r.length),i=_t[e];i?a[i]=t.entity_id:o[e]=t.entity_id}const n=t=>{const e=o[t];if(!e)throw new yt(`Wake Alarm entity for "${t}" is missing from the registry. Make sure the integration is fully loaded.`);return e};for(const t of gt)if(!a[t])throw new yt(`Wake Alarm day toggle for "${t}" is missing from the registry. Make sure the integration is fully loaded and migrated to v2+.`);const c={};for(const t of vt)c[t]=n(t);const l={};for(const t of ft)l[t]=n(t);const d={};for(const t of bt)d[t]=n(t);return{configEntryId:s,enabled:n("enabled"),active:n("active"),alarmTime:n("alarm_time"),days:a,numbers:c,buttons:l,sensors:d}}(this._config.entity,t)}catch(t){this._resolveError=t instanceof yt?t.message:`Could not resolve wake_alarm entities: ${t}`}}render(){return this._config?this._config.entity?this._resolveError?B`<ha-card><div class="error">${this._resolveError}</div></ha-card>`:this._related&&this.hass?"settings"===this._view?B`
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
        `:B`<ha-card><div class="loading">Loading…</div></ha-card>`:B`<ha-card><div class="loading">
        Pick a Wake Alarm enabled-switch in the visual editor.
      </div></ha-card>`:B``}};Mt.styles=mt,t([pt({attribute:!1})],Mt.prototype,"hass",void 0),t([ut()],Mt.prototype,"_config",void 0),t([ut()],Mt.prototype,"_view",void 0),t([ut()],Mt.prototype,"_related",void 0),t([ut()],Mt.prototype,"_resolveError",void 0),Mt=t([lt("wake-alarm-card")],Mt),window.customCards=window.customCards??[],window.customCards.push({type:"wake-alarm-card",name:"Wake Alarm",description:"Wake-up alarm with a gradual light ramp and a music sequence.",preview:!1}),console.info("%c WAKE-ALARM-CARD %c v0.4.0-beta.1 ","color: white; background: #ff5722; font-weight: 700;","color: #ff5722; background: white; font-weight: 700;");export{Mt as WakeAlarmCard};
