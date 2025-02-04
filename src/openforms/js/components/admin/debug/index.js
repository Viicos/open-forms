import PropTypes from 'prop-types';
import React from 'react';
import {IntlProvider} from 'react-intl';
import ReactModal from 'react-modal';

import ComplexProcessVariable from 'components/admin/form_design/registrations/camunda/ComplexProcessVariable';
import {ComponentsContext} from 'components/admin/forms/Context';

const allComponents = {
  comp1: {
    type: 'textfield',
    stepLabel: 'Stap 1: Component 1',
  },
  comp2: {
    type: 'textfield',
    stepLabel: 'Stap 1: Component 2',
  },
  comp3: {
    type: 'textfield',
    stepLabel: 'Stap 2: Component 1',
  },
};

const definition = [
  {
    source: 'interpolate',
    definition: {
      cat: ['interpolation test: ', {var: 'comp2'}],
    },
  },
];

const Debug = () => {
  return (
    <IntlProvider messages={{}} locale="en" defaultLocale="en">
      <ComponentsContext.Provider value={allComponents}>
        <div style={{position: 'relative'}}>
          <ComplexProcessVariable
            name="debug"
            type="array"
            definition={definition}
            onConfirm={console.log}
          />
        </div>
      </ComponentsContext.Provider>
    </IntlProvider>
  );
};

Debug.propTypes = {};

ReactModal.setAppElement(document.getElementById('react'));

export default Debug;
