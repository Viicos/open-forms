import {Formio} from 'formiojs';

import {CLEAR_ON_HIDE, HIDDEN, KEY, LABEL, TOOLTIP} from 'components/form/edit/options';
import {ADVANCED, TRANSLATIONS} from 'components/form/edit/tabs';

import {localiseSchema} from './i18n';

const FormioFieldSet = Formio.Components.components.fieldset;

const FIELDSET_BASIC = {
  key: 'display',
  label: 'Display',
  components: [
    LABEL,
    KEY,
    TOOLTIP,
    HIDDEN,
    CLEAR_ON_HIDE,
    {
      type: 'checkbox',
      key: 'hideHeader',
      label: 'Hide fieldset header',
      tooltip: 'Hide the line and the label above the fieldset in the form',
      defaultValue: false,
    },
  ],
};

class FieldSet extends FormioFieldSet {
  static schema(...extend) {
    return localiseSchema(FormioFieldSet.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...FormioFieldSet.builderInfo,
      schema: FieldSet.schema(),
    };
  }

  static editForm(...extend) {
    const parentEditForm = FormioFieldSet.editForm();
    parentEditForm.components[0].components = [
      FIELDSET_BASIC,
      // The 'API' tab is removed, since the only useful attribute it contained was the 'key', but we
      // have this field in the FIELDSET_BASIC tab.
      // The Conditions and Layout tabs have also been removed since they are not used
      ADVANCED,
      TRANSLATIONS,
    ];
    return parentEditForm;
  }
}

export default FieldSet;
