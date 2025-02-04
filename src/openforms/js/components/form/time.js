import {Formio} from 'formiojs';

import {MAXIMUM_TIME, MIMINUM_TIME} from './edit/options';
import DEFAULT_TABS, {
  ADVANCED,
  REGISTRATION,
  SENSITIVE_BASIC,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';
import {getValidationEditForm} from './edit/validationEditFormUtils';
import {localiseSchema} from './i18n';

const Time = Formio.Components.components.time;

/**
 * Time 24h format is functional by not using the HTML5 widget, but rather the mask
 * input & specify the moment format to use. This still runs the validation and allows
 * us to enter times in 24h notation.
 */
class TimeField extends Time {
  static schema(...extend) {
    const schema = Time.schema(
      {
        inputType: 'text',
        format: 'HH:mm',
        minTime: null,
        maxTime: null,
        validateOn: 'blur',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Time',
      icon: 'clock-o',
      group: 'basic',
      weight: 10,
      schema: TimeField.schema(),
    };
  }

  static editForm() {
    const VALIDATION_TAB = getValidationEditForm({
      ...VALIDATION,
      components: [...VALIDATION.components, MIMINUM_TIME, MAXIMUM_TIME],
    });
    const TABS = {
      ...DEFAULT_TABS,
      components: [SENSITIVE_BASIC, ADVANCED, VALIDATION_TAB, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }

  get defaultSchema() {
    return TimeField.schema();
  }
}

export default TimeField;
