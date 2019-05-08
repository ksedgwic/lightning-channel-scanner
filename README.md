#### How often do Unilateral Closes and Breach Remedy Transactions occur?

![Unilateral Channel Closes](./unilateral.png)

![Breach Remedy Closes](./remedy.png)


#### Methodology

Scanned all inputs in the bitcoin blockchain from 1-Jan-2018 looking
for the segwit script:
```
OP_IF
  <secret>
OP_ELSE
  <nblocks>
  OP_CHECKSEQUENCEVERIFY
  OP_DROP
  <address>
OP_ENDIF
OP_CHECKSIG
```

Tallied matching transactions as 'UNILATERAL' if the argument at the
top of the stack was false and 'REMEDY' if true.

```
1516465683 2018-01-20 16:28:03 505200 UNILATERAL 8dfa5795684c27643e6025477bad476d588ad241f32ed323d370ae0a3c3f07a8 144 144
1516470452 2018-01-20 17:47:32 505209 REMEDY     59d7f39c5ae033d26a976b0dba981f0f7c60bcf5e96df267ee78754c0d31d332 144 2
```
