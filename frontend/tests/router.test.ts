import { describe, expect, it } from 'vitest';
import { parseRoute } from '../src/app/router';

describe('router', () => {
  it('parses menu routes', () => {
    expect(parseRoute('#/')).toEqual({ name: 'home' });
    expect(parseRoute('#/apolices/nova')).toEqual({ name: 'policy-new' });
    expect(parseRoute('#/comparar?a=pol_1&b=pol_2')).toEqual({
      name: 'compare',
      policyAId: 'pol_1',
      policyBId: 'pol_2',
    });
    expect(parseRoute('#/conceitos/DO-036')).toEqual({
      name: 'concept-detail',
      conceptId: 'DO-036',
    });
    expect(parseRoute('#/historico')).toEqual({ name: 'history' });
    expect(parseRoute('#/qualquer')).toEqual({ name: 'not-found' });
  });
});
