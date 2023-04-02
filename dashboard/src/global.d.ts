// global.d.ts
declare module "bootstrap" {
    global {
        interface Window {
            bootstrap: typeof import("bootstrap");
        }
    }
}
